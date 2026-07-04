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
