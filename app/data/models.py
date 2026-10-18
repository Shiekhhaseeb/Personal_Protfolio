from pydantic import BaseModel, Field


class Profile(BaseModel):
    name: str
    title: str
    tagline: str
    location: str
    experience_years: int
    email: str
    photo: str
    bio: str
    current_status: str
    availability: str
    last_updated: str


class Stat(BaseModel):
    label: str
    value: str


class SocialLinks(BaseModel):
    linkedin: str
    github: str
    twitter: str


class SkillsGrouped(BaseModel):
    core: list[str]
    frameworks: list[str]
    mlops: list[str]
    databases: list[str]
    tools: list[str]


class Project(BaseModel):
    id: str
    title: str
    company: str | None = None
    problem: str
    description: str
    tech_stack: list[str]
    role: str
    badges: list[str] = Field(default_factory=list)
    is_proprietary: bool = False
    github_url: str | None = None
    demo_url: str | None = None
    company_url: str | None = None


class Experience(BaseModel):
    company: str
    title: str
    location: str
    duration: str
    url: str | None = None
    bullets: list[str] = Field(default_factory=list)
    current: bool = False
    end_date: str | None = None


class Education(BaseModel):
    degree: str
    institution: str
    duration: str


class Assistant(BaseModel):
    name: str
    initials: str
    greeting: str
    suggested_questions: list[str] = Field(default_factory=list)


class ChatConfig(BaseModel):
    suggestion_chips: list[str] = Field(default_factory=list)


class SeoConfig(BaseModel):
    title: str
    description: str
    og_image: str = "/static/images/og-image.png"
    site_url: str = "https://sheikh-haseeb.onrender.com"


class PortfolioData(BaseModel):
    profile: Profile
    stats: list[Stat]
    social: SocialLinks
    skills: SkillsGrouped
    differentiators: list[str]
    projects_description: str = (
        "RAG systems, computer vision, and ML-powered products — including proprietary builds and open-source contributions."
    )
    projects: list[Project]
    experience: list[Experience]
    education: list[Education]
    certifications: list[str]
    streamlit_demo_url: str | None = None
    assistant: Assistant
    chat: ChatConfig = Field(default_factory=ChatConfig)
    seo: SeoConfig = Field(
        default_factory=lambda: SeoConfig(
            title="Sheikh Haseeb — AI/ML Engineer",
            description="Portfolio and RAG assistant of Sheikh Haseeb, an AI/ML Engineer specializing in LangChain, RAG systems, and agentic AI architectures.",
            og_image="/static/images/og-image.png",
            site_url="https://sheikh-haseeb.onrender.com",
        )
    )


