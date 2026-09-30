from core.documents import make_cam, make_letter
from core.reference import MEENA


def test_make_cam():
    doc = make_cam(MEENA)
    assert isinstance(doc, bytes)
    content = doc.decode("utf-8")
    assert MEENA["id"] in content
    assert "Version: stub_model_v1" in content

def test_make_letter():
    doc = make_letter(MEENA, lang="hi")
    assert isinstance(doc, bytes)
    content = doc.decode("utf-8")
    assert MEENA["id"] in content
    assert "Version: stub_letter_v1" in content
    assert "PENDING NATIVE REVIEW" in content

    doc_en = make_letter(MEENA, lang="en")
    assert "PENDING NATIVE REVIEW" not in doc_en.decode("utf-8")
