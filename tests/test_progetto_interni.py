"""Unit tests for the composed progetto_interni workflow."""
from __future__ import annotations

from lovarch_cli.ai import AiImageResult, AiTextResult
from lovarch_cli.workflows.progetto import progetto_interni


class _FakeGateway:
    """Fakes agent text calls, image calls and user-context."""

    def __init__(self, *, render_fails=False):
        self.render_fails = render_fails
        self.text_calls = 0
        self.image_calls = 0

    async def get_user_context(self, *, lead_id=None):
        return {"prompt_block": "Studio Test.", "preferences": {"preferred_language": "it"}}

    async def generate_text(self, prompt, *, role="executor", **kwargs):
        self.text_calls += 1
        return AiTextResult(text=f"testo #{self.text_calls}", model="anthropic/claude-sonnet-5",
                            input_tokens=10, output_tokens=20, credits_charged=3,
                            balance=100, is_admin=False)

    async def generate_image(self, prompt, *, quality="medium", aspect="16:9", operation_type=None):
        self.image_calls += 1
        if self.render_fails:
            from lovarch_cli.ai import AiGatewayError
            raise AiGatewayError("render down")
        return AiImageResult(image_bytes=b"PNGDATA", content_type="image/png",
                             revised_prompt=None, credits_charged=53,
                             balance=47, is_admin=False)


async def test_progetto_concept_only():
    gw = _FakeGateway()
    r = await progetto_interni(gw, "attico 90mq", want_render=False, want_preventivo=False)
    assert "concept" in r.sections
    assert r.renders == []
    assert "preventivo" not in r.sections
    assert r.credits_charged == 3          # only interior-designer
    assert "# Progetto di interni" in r.dossier_md
    assert "BOZZA" in r.dossier_md


async def test_progetto_full_chain():
    gw = _FakeGateway()
    r = await progetto_interni(gw, "attico 90mq", want_render=True, want_preventivo=True,
                               render_count=2, language="it")
    assert gw.image_calls == 2
    assert len(r.renders) == 2
    assert "preventivo" in r.sections
    # interior(3) + preventivo(3) + 2 renders(53*2)
    assert r.credits_charged == 3 + 3 + 53 * 2
    assert "## Render" in r.dossier_md
    assert "## Preventivo" in r.dossier_md


async def test_progetto_render_failure_is_warning_not_crash():
    gw = _FakeGateway(render_fails=True)
    r = await progetto_interni(gw, "loft", want_render=True, want_preventivo=False)
    assert r.renders == []
    assert any("render" in w for w in r.warnings)
    assert "concept" in r.sections     # concept still delivered


async def test_cantiere_check_full():
    from lovarch_cli.workflows.progetto import cantiere_check
    gw = _FakeGateway()
    r = await cantiere_check(gw, "ristrutturazione 120mq, 3 imprese", want_sicurezza=True)
    assert "cronoprogramma" in r.sections
    assert "sicurezza" in r.sections
    assert r.credits_charged == 6   # direzione(3) + sicurezza(3)
    assert "# Cantiere" in r.dossier_md
    assert "BOZZA" in r.dossier_md


async def test_cantiere_no_sicurezza():
    from lovarch_cli.workflows.progetto import cantiere_check
    gw = _FakeGateway()
    r = await cantiere_check(gw, "opere minori", want_sicurezza=False)
    assert "sicurezza" not in r.sections
    assert r.credits_charged == 3


async def test_progetto_completo_plan_only():
    from lovarch_cli.workflows.progetto import progetto_completo
    import json as _json
    class _PlanGW(_FakeGateway):
        async def generate_text(self, prompt, *, role="executor", **kw):
            self.text_calls += 1
            if role == "chief":
                payload = {"inquadramento":"attico da ristrutturare","agenti":[
                    {"id":"interior-designer","focus":"concept"},
                    {"id":"strutturista","focus":"aperture"}],"note":[]}
                from lovarch_cli.ai import AiTextResult
                return AiTextResult(text=_json.dumps(payload),model="anthropic/claude-opus-4.8",
                                    input_tokens=5,output_tokens=10,credits_charged=8,balance=90,is_admin=False)
            return await super().generate_text(prompt, role=role, **kw)
    gw=_PlanGW()
    r=await progetto_completo(gw,"attico 90mq da ristrutturare",esegui=0)
    assert len(r.plan["agenti"])==2
    assert r.sections == {}          # esegui=0 → non lancia
    assert r.credits_charged==8      # solo il chief
    assert "## Piano" in r.dossier_md


async def test_progetto_completo_esegui():
    from lovarch_cli.workflows.progetto import progetto_completo
    import json as _json
    from lovarch_cli.ai import AiTextResult
    class _PlanGW(_FakeGateway):
        async def get_user_context(self, *, lead_id=None):
            return {"prompt_block":"Studio X.","preferences":{"preferred_language":"it"}}
        async def generate_text(self, prompt, *, role="executor", **kw):
            self.text_calls += 1
            if role == "chief":
                payload={"inquadramento":"x","agenti":[{"id":"interior-designer","focus":"c"}],"note":[]}
                return AiTextResult(text=_json.dumps(payload),model="opus",input_tokens=1,output_tokens=1,credits_charged=8,balance=90,is_admin=False)
            return AiTextResult(text="testo agente",model="sonnet",input_tokens=1,output_tokens=1,credits_charged=3,balance=87,is_admin=False)
    gw=_PlanGW()
    r=await progetto_completo(gw,"attico",esegui=2)
    assert "interior-designer" in r.sections
    assert r.credits_charged==8+3    # chief + 1 agente
