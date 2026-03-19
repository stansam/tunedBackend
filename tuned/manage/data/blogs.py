from datetime import datetime, timedelta

blogCategories = [
    {
        "name": "Academic Writing",
        "slug": "academic-writing",
        "description": "Tips, guides, and best practices for effective academic writing.",
        "image": "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=800&q=80",
    },
    {
        "name": "Research Methods",
        "slug": "research-methods",
        "description": "Insights into quantitative, qualitative, and mixed-method research.",
        "image": "https://images.unsplash.com/photo-1532012197267-da84d127e765?w=800&q=80",
    },
    {
        "name": "Student Life",
        "slug": "student-life",
        "description": "Advice for balancing academics, productivity, and personal well-being.",
        "image": "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=800&q=80",
    },
    {
        "name": "Career & Professional Development",
        "slug": "career-professional-development",
        "description": "Guidance on CVs, cover letters, interviews, and career growth.",
        "image": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&q=80",
    },
]

blogPosts = [
    {
        "title": "How to Write an Effective Thesis Statement",
        "content": (
            "<p>A strong thesis statement is essential for any academic paper. "
            "It distils your argument into a single claim that guides your reader throughout the essay.</p>"
            "<p>This article provides step-by-step guidance on crafting clear, concise, and compelling "
            "thesis statements for essays, dissertations, and research papers alike.</p>"
        ),
        "excerpt": "Learn how to create powerful thesis statements that effectively communicate your paper's main argument.",
        "author": "Vin Vincent",
        "category_slug": "academic-writing",
        "tags": "thesis statement, academic writing, essay tips",
        "is_published": True,
        "is_featured": True,
        "published_at": datetime.now() - timedelta(days=1),
        "featured_image": "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=1200&q=80",
        "meta_description": "Step-by-step guide to writing a powerful thesis statement for academic essays, dissertations, and research papers.",
    },
    {
        "title": "Quantitative vs. Qualitative Research: Choosing the Right Approach",
        "content": (
            "<p>Understanding the differences between quantitative and qualitative research is crucial "
            "for designing effective studies.</p>"
            "<p>This article compares the methodologies, data collection techniques, and analysis methods "
            "of both approaches, helping you choose the one that best fits your research question.</p>"
        ),
        "excerpt": "A comprehensive comparison of quantitative and qualitative research methodologies.",
        "author": "Mark Twain",
        "category_slug": "research-methods",
        "tags": "quantitative research, qualitative research, research design, methodology",
        "is_published": True,
        "is_featured": True,
        "published_at": datetime.now() - timedelta(days=3),
        "featured_image": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&q=80",
        "meta_description": "Compare quantitative and qualitative research approaches and learn how to pick the right one for your study.",
    },
    {
        "title": "Time Management Strategies for Academic Success",
        "content": (
            "<p>Effective time management is the cornerstone of academic achievement. Students who master "
            "the art of balancing study schedules, assignment deadlines, and personal commitments often "
            "find themselves less stressed and more productive.</p>"
            "<p>This guide explores the Pomodoro Technique, time-blocking methods, and priority matrix "
            "frameworks. We also cover how to create realistic study schedules that accommodate your "
            "learning style and lifestyle demands.</p>"
            "<p>From digital tools like calendar apps and task managers to healthy study habits, "
            "this article provides actionable strategies that can transform your academic performance.</p>"
        ),
        "excerpt": "Discover proven time management techniques to enhance your academic performance while maintaining a healthy work-life balance.",
        "author": "Barry Allan",
        "category_slug": "student-life",
        "tags": "time management, study tips, productivity, student life, academic success",
        "is_published": True,
        "is_featured": False,
        "published_at": datetime.now() - timedelta(days=7),
        "featured_image": "https://images.unsplash.com/photo-1506784365847-bbad939e9335?w=1200&q=80",
        "meta_description": "Proven time management strategies for students — from Pomodoro to time-blocking — to boost academic performance.",
    },
    {
        "title": "The Art of Citation: Mastering APA, MLA, and Chicago Styles",
        "content": (
            "<p>Proper citation is more than academic courtesy — it demonstrates scholarly integrity and "
            "helps readers trace the sources of your arguments.</p>"
            "<p>This detailed guide breaks down APA 7th, MLA 9th, and Chicago 17th edition styles, "
            "covering in-text citations, reference lists, and bibliographies with practical examples.</p>"
            "<p>We also cover common mistakes, tools that streamline the process, and how proper "
            "citation protects your academic integrity and intellectual property rights.</p>"
        ),
        "excerpt": "A comprehensive guide to mastering APA, MLA, and Chicago citation styles with practical examples.",
        "author": "Billy The Kid",
        "category_slug": "academic-writing",
        "tags": "citation styles, APA, MLA, Chicago, academic writing, referencing, plagiarism",
        "is_published": True,
        "is_featured": False,
        "published_at": datetime.now() - timedelta(days=14),
        "featured_image": "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=1200&q=80",
        "meta_description": "Comprehensive guide to APA, MLA, and Chicago citation styles with examples and tips for avoiding plagiarism.",
    },
    {
        "title": "Crafting a Winning CV: What Employers Actually Look For",
        "content": (
            "<p>In a competitive job market, your CV is your first impression. Recruiters spend an average "
            "of just seven seconds scanning a CV, so every word must count.</p>"
            "<p>This article covers how to structure your CV, tailor it for specific roles, choose the "
            "right format (chronological vs. functional), and avoid the most common mistakes that land "
            "applications in the reject pile.</p>"
            "<p>Whether you are a fresh graduate or an experienced professional, these strategies will "
            "help you present your skills in the most compelling way possible.</p>"
        ),
        "excerpt": "Learn what recruiters actually want to see in a CV and how to make yours stand out from the competition.",
        "author": "Sarah Collins",
        "category_slug": "career-professional-development",
        "tags": "CV writing, resume, career advice, job search, professional development",
        "is_published": True,
        "is_featured": True,
        "published_at": datetime.now() - timedelta(days=4),
        "featured_image": "https://images.unsplash.com/photo-1586281380349-632531db7ed4?w=1200&q=80",
        "meta_description": "Expert tips on crafting a CV that impresses recruiters — structure, format, tailoring, and common mistakes to avoid.",
    },
    {
        "title": "Understanding the Dissertation Proposal: A Step-by-Step Guide",
        "content": (
            "<p>The dissertation proposal is the first official milestone of your research journey. "
            "A well-crafted proposal establishes your research question, methodology, and significance, "
            "and will form the backbone of your entire dissertation.</p>"
            "<p>In this guide we walk through every section — from the introduction and literature review "
            "to the methodology and ethical considerations — with annotated examples at each stage.</p>"
        ),
        "excerpt": "A step-by-step breakdown of how to write a compelling dissertation proposal that gets approved.",
        "author": "Vin Vincent",
        "category_slug": "academic-writing",
        "tags": "dissertation, proposal, research, academic writing, methodology",
        "is_published": False,
        "is_featured": False,
        "published_at": None,
        "featured_image": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=1200&q=80",
        "meta_description": "Step-by-step guide to writing a winning dissertation proposal — structure, tips, and annotated examples.",
    },
    {
        "title": "Mastering the Art of Public Speaking in Academia",
        "content": (
            "<p>Public speaking is a vital skill for presenting research findings, teaching, and defending your thesis.</p>"
            "<p>This article explores effective techniques to conquer stage fright, structure your presentations logically, and engage your audience.</p>"
            "<p>Learn how to design impactful slides and deliver your message with confidence and clarity.</p>"
        ),
        "excerpt": "A comprehensive guide to improving your academic presentation skills and conquering stage fright.",
        "author": "Dr. Sarah Ochieng",
        "category_slug": "student-life",
        "tags": "public speaking, presentations, student life, academic success",
        "is_published": True,
        "is_featured": True,
        "published_at": datetime.now() - timedelta(days=2),
        "featured_image": "https://images.unsplash.com/photo-1475721028070-dfc798ce0a90?w=1200&q=80",
        "meta_description": "Enhance your academic public speaking skills and deliver presentations with confidence and clarity.",
    },
    {
        "title": "Writing a Strong Literature Review: Tips and Tricks",
        "content": (
            "<p>A literature review is more than a summary; it's a critical synthesis of existing research.</p>"
            "<p>Discover how to effectively search for scholarly articles, organize your findings thematically, and identify gaps in the literature.</p>"
            "<p>This step-by-step guide helps you lay a solid theoretical foundation for your academic projects.</p>"
        ),
        "excerpt": "Learn how to conduct and write a comprehensive and critical literature review.",
        "author": "Amina Waweru",
        "category_slug": "academic-writing",
        "tags": "literature review, research, academic writing, synthesis",
        "is_published": True,
        "is_featured": True,
        "published_at": datetime.now() - timedelta(days=5),
        "featured_image": "https://images.unsplash.com/photo-1455390582262-044cdead277a?w=1200&q=80",
        "meta_description": "Step-by-step guide to finding, analyzing, and synthesizing scholarly sources for your literature review.",
    },
    {
        "title": "The Essential Guide to Networking for Researchers",
        "content": (
            "<p>Building a robust professional network is crucial for collaborative research and career advancement.</p>"
            "<p>This post discusses effective strategies for connecting with peers and mentors at academic conferences and through digital platforms.</p>"
            "<p>Learn how to craft an impactful elevator pitch, follow up meaningfully, and cultivate lasting academic relationships.</p>"
        ),
        "excerpt": "Effective networking strategies to advance your academic career and foster research collaborations.",
        "author": "James Kariuki",
        "category_slug": "career-professional-development",
        "tags": "networking, academic career, professional development, conferences",
        "is_published": True,
        "is_featured": True,
        "published_at": datetime.now() - timedelta(days=8),
        "featured_image": "https://images.unsplash.com/photo-1515162816999-a0c47dc192f7?w=1200&q=80",
        "meta_description": "A guide for researchers on how to build and maintain a strong professional network both online and offline.",
    },
]