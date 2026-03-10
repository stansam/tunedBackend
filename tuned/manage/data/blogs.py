from datetime import datetime, timedelta

blogCategories = [
    {
        "name": "Academic Writing",
        "slug": "academic-writing",
        "description": "Tips and guides for academic writing"
    },
    {
        "name": "Research Methods",
        "slug": "research-methods",
        "description": "Insights into effective research methodologies"
    },
    {
        "name": "Student Life",
        "slug": "student-life",
        "description": "Advice for balancing academics and personal life"
    }
]

blogPosts = [
    {
        "title": "How to Write an Effective Thesis Statement",
        "content": "<p>A strong thesis statement is essential for any academic paper...</p><p>This article provides step-by-step guidance on crafting clear, concise, and compelling thesis statements...</p>",
        "excerpt": "Learn how to create powerful thesis statements that effectively communicate your paper's main argument.",
        "author": "Vin Vincent",
        "category": blogCategories[0],
        "tags": "thesis statement, academic writing, essay tips",
        "is_published": True,
        "published_at": datetime.now()
    },
    {
        "title": "Quantitative vs. Qualitative Research: Choosing the Right Approach",
        "content": "<p>Understanding the differences between quantitative and qualitative research is crucial for designing effective studies...</p><p>This article compares the methodologies, data collection techniques, and analysis methods of both approaches...</p>",
        "excerpt": "A comprehensive comparison of quantitative and qualitative research methodologies to help you choose the right approach for your study.",
        "author": "Mark Twain",
        "category": blogCategories[1],
        "tags":"quantitative research, qualitative research, research methods",
        "is_published": True,
        "published_at": datetime.now()
    },
    {
        "title": "Time Management Strategies for Academic Success",
        "content": "<p>Effective time management is the cornerstone of academic achievement. Students who master the art of balancing study schedules, assignment deadlines, and personal commitments often find themselves less stressed and more productive.</p><p>This comprehensive guide explores proven techniques such as the Pomodoro Technique, time-blocking methods, and priority matrix frameworks. We'll also discuss how to create realistic study schedules that accommodate your learning style and lifestyle demands.</p><p>From utilizing digital tools like calendar apps and task managers to developing healthy study habits, this article provides actionable strategies that can transform your academic performance and overall well-being.</p>",
        "excerpt": "Discover proven time management techniques and strategies to enhance your academic performance while maintaining a healthy work-life balance.",
        "author": "Barry Allan",
        "category": blogCategories[2],  # Student Life
        "tags": "time management, study tips, productivity, student life, academic success",
        "is_published": True,
        "published_at": datetime.now() - timedelta(days=7)
    },
    {
        "title": "The Art of Citation: Mastering APA, MLA, and Chicago Styles",
        "content": "<p>Proper citation is more than just academic courtesy—it's a fundamental skill that demonstrates scholarly integrity and helps readers trace the sources of your arguments and evidence.</p><p>This detailed guide breaks down the three most commonly used citation styles in academic writing: APA (American Psychological Association), MLA (Modern Language Association), and Chicago Manual of Style. Each style serves different disciplines and has unique formatting requirements for in-text citations, reference lists, and bibliographies.</p><p>We'll explore practical examples, common mistakes to avoid, and tools that can streamline your citation process. Whether you're writing a psychology research paper, a literature analysis, or a historical thesis, understanding these citation styles will elevate the professionalism of your work.</p><p>Additionally, we'll discuss the importance of avoiding plagiarism and how proper citation practices protect both your academic integrity and intellectual property rights.</p>",
        "excerpt": "A comprehensive guide to mastering APA, MLA, and Chicago citation styles with practical examples and tips for avoiding common formatting mistakes.",
        "author": "Billy The Kid",
        "category": blogCategories[0],  # Academic Writing
        "tags": "citation styles, APA, MLA, Chicago, academic writing, referencing, plagiarism",
        "is_published": True,
        "published_at": datetime.now() - timedelta(days=14)
    }
]