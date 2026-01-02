"""Built-in skills from Anthropic's official skills repository.

These skills provide specialized capabilities for common tasks like
document processing, design, and development.
"""

from .communication_skills import (
    DocCoauthoringSkill,
    InternalCommsSkill,
    SlackGifCreatorSkill,
)
from .design_skills import (
    AlgorithmicArtSkill,
    BrandGuidelinesSkill,
    CanvasDesignSkill,
    FrontendDesignSkill,
    ThemeFactorySkill,
)
from .development_skills import (
    MCPBuilderSkill,
    SkillCreatorSkill,
    WebappTestingSkill,
    WebArtifactsBuilderSkill,
)
from .document_skills import DocxSkill, PDFSkill, PPTXSkill, XLSXSkill

__all__ = [
    # Document Skills
    "PDFSkill",
    "DocxSkill",
    "PPTXSkill",
    "XLSXSkill",
    # Design Skills
    "FrontendDesignSkill",
    "CanvasDesignSkill",
    "AlgorithmicArtSkill",
    "BrandGuidelinesSkill",
    "ThemeFactorySkill",
    # Development Skills
    "MCPBuilderSkill",
    "SkillCreatorSkill",
    "WebArtifactsBuilderSkill",
    "WebappTestingSkill",
    # Communication Skills
    "DocCoauthoringSkill",
    "InternalCommsSkill",
    "SlackGifCreatorSkill",
]
