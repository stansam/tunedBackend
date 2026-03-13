service_categories_dict = {
    "Proofreading and Editing": [
        ("Proofreading",
        "Covers dissertations, theses, articles, essays, resumes, business documents & more—primarily catching any remaining errors in spelling, grammar, and punctuation before publication."),
        ("Copyediting",
        "Focuses on grammar, spelling, punctuation, consistency, clarity and adherence to style guides—improving readability and sentence structure."),
        ("AI Content Editing",
        "Removal of AI-detected content and humanization of AI-written text."),
        ("Reviewing and Rewriting Services",
        "Rewrite, review, revamp or repurpose your content—ideal for personal statements, manuscripts, plagiarism removal, and clarity."),
        ("Citation and Formatting",
        "Handles APA, MLA, Chicago, Harvard, IEEE, OSCOLA and more."),
    ],
    "Writing": [
        ("Essays",               "Custom essay writing."),
        ("Research Papers",      "In-depth academic research."),
        ("Dissertations",        "Comprehensive dissertation help."),
        ("Case Studies",         "Analytical case studies."),
        ("Courseworks",          "Well-researched coursework."),
        ("Term Papers",          "Academic term paper writing."),
        ("Admission Essays",     "Essays for college admissions."),
        ("College Papers",       "Academic papers across subjects."),
        ("Annotated Bibliographies", "Annotated source lists."),
        ("Literature Review",    "Thorough source reviews."),
        ("Capstone Project",     "Final project support."),
    ],
    "Data Analysis": [
        ("SPSS",    "Statistical analysis using SPSS."),
        ("STATA",   "Econometrics and regressions."),
        ("R",       "Statistical computing with R."),
        ("NVivo",   "Qualitative analysis with NVivo."),
        ("Excel",   "Data modelling and visualization."),
        ("Python",  "Python-based data science."),
        ("Power BI","Interactive dashboards."),
        ("Tableau", "Visual analytics with Tableau."),
    ],
    "Business and Market Research": [
        ("Business Plans",      "Investor-ready business plans."),
        ("Proposals",           "Professional proposals."),
        ("Grant Writing",       "Tailored grant applications."),
        ("Market Research",     "Data-driven market analysis."),
        ("Competitor Analysis", "In-depth competitor landscapes.",       ),
        ("SWOT Analysis",       "SWOT framework analysis."),
        ("PESTLE Analysis",     "Macro-environmental scan."),
    ],
    "Presentations": [
        ("PowerPoint Presentations",      "Custom PowerPoint decks."),
        ("Google Slides Presentations",   "Polished Google Slides decks."),
        ("Academic & Business Pitch Decks","High-impact pitch decks."),
    ],
    "Resume Writing": [
        ("CV & Resume Creation",           "Job-winning CVs & resumes."),
        ("Cover Letters",                  "Compelling cover letters."),
        ("LinkedIn Profile Optimization",  "LinkedIn profile makeover."),
    ],
    "Technical Writing & Calculations": [
        ("Technical reports, manuals, and documentation",
        "Detailed technical writing and documentation."),
        ("Quantitative coursework",
        "Help with Algebra, Calculus, Stats, Accounting, Finance, Engineering problems."),
    ],
}

service_to_pricing_category_dict = {
    # Writing services -> "Writing" pricing category
    "Essays": "Writing",
    "Research Papers": "Writing",
    "Dissertations": "Writing",
    "Case Studies": "Writing",
    "Courseworks": "Writing",
    "Term Papers": "Writing",
    "Admission Essays": "Writing",
    "College Papers": "Writing",
    "Annotated Bibliographies": "Writing",
    "Literature Review": "Writing",
    "Capstone Project": "Writing",
    
    # Proofreading and Editing services -> "Proofreading & Editing" pricing category
    "Proofreading": "Proofreading & Editing",
    "Copyediting": "Proofreading & Editing",
    "Reviewing and Rewriting Services": "Proofreading & Editing",
    "Citation and Formatting": "Proofreading & Editing",
    
    # AI Content Editing -> "Humanizing AI" pricing category
    "AI Content Editing": "Humanizing AI",
    
    # Technical services -> "Technical & Calculations" pricing category
    "Technical reports, manuals, and documentation": "Technical & Calculations",
    "Quantitative coursework": "Technical & Calculations",
    
    # Data Analysis services -> "Technical & Calculations" pricing category
    "SPSS": "Technical & Calculations",
    "STATA": "Technical & Calculations",
    "R": "Technical & Calculations",
    "NVivo": "Technical & Calculations",
    "Excel": "Technical & Calculations",
    "Python": "Technical & Calculations",
    "Power BI": "Technical & Calculations",
    "Tableau": "Technical & Calculations",
    
    # Business and Market Research -> "Writing" pricing category
    "Business Plans": "Writing",
    "Proposals": "Writing",
    "Grant Writing": "Writing",
    "Market Research": "Writing",
    "Competitor Analysis": "Writing",
    "SWOT Analysis": "Writing",
    "PESTLE Analysis": "Writing",
    
    # Presentations -> "Writing" pricing category
    "PowerPoint Presentations": "Writing",
    "Google Slides Presentations": "Writing",
    "Academic & Business Pitch Decks": "Writing",
    
    # Resume Writing -> "Writing" pricing category
    "CV & Resume Creation": "Writing",
    "Cover Letters": "Writing",
    "LinkedIn Profile Optimization": "Writing",
}
service_category_descriptions_dict = {
    "Proofreading and Editing": "Whether it is an academic paper, resume, or business document, professional proofreading helps you eliminate errors and improve clarity, style, and coherence.",
    "Writing": "From essays and dissertations to admission papers, we support you in producing structured, original, well-researched and referenced and compelling writing that meets academic and professional standards.",
    "Data Analysis": "Make sense of your data and uncover key insights with accurate analysis, visualizations, and interpretation using trusted tools and methods.",
    "Business and Market Research": "Strengthen your business strategy with detailed, data-driven research. Gain insights into competitors, markets, and industry trends that support smart decisions and professional reports.",
    "Presentations": "Impress your audience with visually engaging, professionally designed presentations. Communicate complex ideas clearly and confidently in any setting, academic, business, or creative.",
    "Resume Writing": "Present your experience and skills in the best possible light. Whether you’re applying for your first job or making a career move, we help you create a strong, customized resume and cover letter.",
    "Technical Writing & Calculations": "Break down complex ideas into clear, well-structured content. From scientific reports to math-based tasks, this service helps you communicate technical details accurately and efficiently."
}