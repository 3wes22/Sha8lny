export interface Question {
  id: string;
  type: "multiple-choice" | "slider" | "code" | "drag-drop" | "text";
  question: string;
  questionAr?: string;
  options?: string[];
  optionsAr?: string[];
  correctAnswer?: any;
  codeLanguage?: string;
  testCases?: { input: string; expected: string }[];
  min?: number;
  max?: number;
  labels?: { [key: number]: string };
  labelsAr?: { [key: number]: string };
  items?: string[];
  itemsAr?: string[];
  hint?: string;
  hintAr?: string;
}

export interface Category {
  id: string;
  name: string;
  nameAr: string;
  icon: string;
  estimatedTime: number;
  status: "completed" | "in-progress" | "not-started" | "locked";
  questions: Question[];
}

export const assessmentData = {
  categories: [
    {
      id: "technical",
      name: "Technical Skills",
      nameAr: "المهارات التقنية",
      icon: "💻",
      estimatedTime: 20,
      status: "in-progress" as const,
      questions: [
        {
          id: "tech-1",
          type: "slider" as const,
          question: "Rate your proficiency in Python programming:",
          questionAr: "قيم مستوى إتقانك لبرمجة بايثون:",
          min: 1,
          max: 10,
          labels: {
            1: "Beginner",
            5: "Intermediate",
            10: "Expert"
          },
          labelsAr: {
            1: "مبتدئ",
            5: "متوسط",
            10: "خبير"
          },
          correctAnswer: 5
        },
        {
          id: "tech-2",
          type: "multiple-choice" as const,
          question: "Which of the following is NOT a Python web framework?",
          questionAr: "أي مما يلي ليس إطار عمل ويب بايثون؟",
          options: [
            "Django",
            "Flask",
            "FastAPI",
            "React"
          ],
          optionsAr: [
            "Django",
            "Flask",
            "FastAPI",
            "React"
          ],
          correctAnswer: "React",
          hint: "Think about which one is a JavaScript framework"
        },
        {
          id: "tech-3",
          type: "code" as const,
          question: "Write a function to reverse a string in Python:",
          questionAr: "اكتب دالة لعكس سلسلة نصية في بايثون:",
          codeLanguage: "python",
          testCases: [
            { input: "hello", expected: "olleh" },
            { input: "world", expected: "dlrow" },
            { input: "python", expected: "nohtyp" }
          ],
          correctAnswer: "def reverse_string(s):\n    return s[::-1]"
        },
        {
          id: "tech-4",
          type: "multiple-choice" as const,
          question: "What does SQL stand for?",
          questionAr: "ماذا يعني SQL؟",
          options: [
            "Structured Query Language",
            "Simple Question Language",
            "Standard Query Logic",
            "System Quality Level"
          ],
          optionsAr: [
            "لغة الاستعلام المهيكلة",
            "لغة الأسئلة البسيطة",
            "منطق الاستعلام القياسي",
            "مستوى جودة النظام"
          ],
          correctAnswer: "Structured Query Language"
        },
        {
          id: "tech-5",
          type: "drag-drop" as const,
          question: "Arrange these steps in the correct order to debug a program:",
          questionAr: "رتب هذه الخطوات بالترتيب الصحيح لتصحيح برنامج:",
          items: [
            "Identify the bug",
            "Reproduce the error",
            "Fix the code",
            "Test the solution",
            "Deploy the fix"
          ],
          itemsAr: [
            "تحديد الخطأ",
            "إعادة إنتاج الخطأ",
            "إصلاح الكود",
            "اختبار الحل",
            "نشر الإصلاح"
          ],
          correctAnswer: [
            "Reproduce the error",
            "Identify the bug",
            "Fix the code",
            "Test the solution",
            "Deploy the fix"
          ]
        }
      ]
    },
    {
      id: "soft-skills",
      name: "Soft Skills",
      nameAr: "المهارات الشخصية",
      icon: "🤝",
      estimatedTime: 15,
      status: "not-started" as const,
      questions: [
        {
          id: "soft-1",
          type: "multiple-choice" as const,
          question: "How would you handle a conflict with a team member?",
          questionAr: "كيف ستتعامل مع صراع مع أحد أعضاء الفريق؟",
          options: [
            "Discuss the issue privately and find common ground",
            "Ignore it and hope it resolves itself",
            "Escalate to management immediately",
            "Avoid working with them"
          ],
          optionsAr: [
            "مناقشة المشكلة بشكل خاص والعثور على أرضية مشتركة",
            "تجاهلها وآمل أن تحل نفسها",
            "التصعيد إلى الإدارة على الفور",
            "تجنب العمل معهم"
          ],
          correctAnswer: "Discuss the issue privately and find common ground"
        },
        {
          id: "soft-2",
          type: "slider" as const,
          question: "Rate your ability to work under pressure:",
          questionAr: "قيم قدرتك على العمل تحت الضغط:",
          min: 1,
          max: 10,
          labels: {
            1: "Poor",
            5: "Good",
            10: "Excellent"
          },
          labelsAr: {
            1: "ضعيف",
            5: "جيد",
            10: "ممتاز"
          },
          correctAnswer: 7
        },
        {
          id: "soft-3",
          type: "multiple-choice" as const,
          question: "What's the most important quality in a team leader?",
          questionAr: "ما هي أهم صفة في قائد الفريق؟",
          options: [
            "Communication skills",
            "Technical expertise",
            "Strict management",
            "Individual performance"
          ],
          optionsAr: [
            "مهارات التواصل",
            "الخبرة التقنية",
            "الإدارة الصارمة",
            "الأداء الفردي"
          ],
          correctAnswer: "Communication skills"
        },
        {
          id: "soft-4",
          type: "text" as const,
          question: "Describe a time when you had to adapt to a major change at work:",
          questionAr: "صف وقتًا اضطررت فيه للتكيف مع تغيير كبير في العمل:",
          hint: "Think about specific examples and outcomes"
        },
        {
          id: "soft-5",
          type: "multiple-choice" as const,
          question: "How do you prioritize tasks when everything seems urgent?",
          questionAr: "كيف تحدد أولويات المهام عندما يبدو كل شيء عاجلاً؟",
          options: [
            "Assess impact and deadlines, then prioritize accordingly",
            "Work on whatever is easiest first",
            "Do everything at once",
            "Ask someone else to decide"
          ],
          optionsAr: [
            "تقييم التأثير والمواعيد النهائية، ثم تحديد الأولويات وفقًا لذلك",
            "العمل على ما هو أسهل أولاً",
            "القيام بكل شيء في وقت واحد",
            "اسأل شخصًا آخر ليقرر"
          ],
          correctAnswer: "Assess impact and deadlines, then prioritize accordingly"
        }
      ]
    },
    {
      id: "language",
      name: "Language Proficiency",
      nameAr: "إتقان اللغة",
      icon: "🗣️",
      estimatedTime: 15,
      status: "not-started" as const,
      questions: [
        {
          id: "lang-1",
          type: "slider" as const,
          question: "Rate your English proficiency level:",
          questionAr: "قيم مستوى إتقانك للغة الإنجليزية:",
          min: 1,
          max: 10,
          labels: {
            1: "Beginner",
            5: "Intermediate",
            10: "Native/Fluent"
          },
          labelsAr: {
            1: "مبتدئ",
            5: "متوسط",
            10: "لغة أم/طليق"
          },
          correctAnswer: 7
        },
        {
          id: "lang-2",
          type: "multiple-choice" as const,
          question: "Choose the correct sentence:",
          questionAr: "اختر الجملة الصحيحة:",
          options: [
            "She don't like coffee",
            "She doesn't likes coffee",
            "She doesn't like coffee",
            "She not like coffee"
          ],
          correctAnswer: "She doesn't like coffee"
        },
        {
          id: "lang-3",
          type: "text" as const,
          question: "Write a brief introduction about yourself in English:",
          questionAr: "اكتب مقدمة موجزة عن نفسك باللغة الإنجليزية:",
          hint: "Include your name, background, and career interests"
        },
        {
          id: "lang-4",
          type: "multiple-choice" as const,
          question: "What is the past tense of 'go'?",
          questionAr: "ما هو الماضي من 'go'؟",
          options: ["goed", "went", "gone", "going"],
          correctAnswer: "went"
        },
        {
          id: "lang-5",
          type: "slider" as const,
          question: "Rate your Arabic proficiency level:",
          questionAr: "قيم مستوى إتقانك للغة العربية:",
          min: 1,
          max: 10,
          labels: {
            1: "Beginner",
            5: "Intermediate",
            10: "Native/Fluent"
          },
          labelsAr: {
            1: "مبتدئ",
            5: "متوسط",
            10: "لغة أم/طليق"
          },
          correctAnswer: 10
        }
      ]
    },
    {
      id: "industry",
      name: "Industry Knowledge",
      nameAr: "المعرفة الصناعية",
      icon: "🏢",
      estimatedTime: 18,
      status: "locked" as const,
      questions: [
        {
          id: "ind-1",
          type: "multiple-choice" as const,
          question: "Which city is known as Egypt's technology hub?",
          questionAr: "أي مدينة تُعرف باسم مركز التكنولوجيا في مصر؟",
          options: ["Cairo", "Alexandria", "Aswan", "Luxor"],
          optionsAr: ["القاهرة", "الإسكندرية", "أسوان", "الأقصر"],
          correctAnswer: "Cairo"
        },
        {
          id: "ind-2",
          type: "slider" as const,
          question: "How familiar are you with the Egyptian job market?",
          questionAr: "ما مدى معرفتك بسوق العمل المصري؟",
          min: 1,
          max: 10,
          labels: {
            1: "Not Familiar",
            5: "Somewhat Familiar",
            10: "Very Familiar"
          },
          labelsAr: {
            1: "غير مألوف",
            5: "مألوف إلى حد ما",
            10: "مألوف جدًا"
          },
          correctAnswer: 6
        },
        {
          id: "ind-3",
          type: "multiple-choice" as const,
          question: "What is the most in-demand tech skill in Egypt currently?",
          questionAr: "ما هي المهارة التقنية الأكثر طلبًا في مصر حاليًا؟",
          options: [
            "Full Stack Development",
            "Data Science",
            "Mobile Development",
            "DevOps"
          ],
          optionsAr: [
            "تطوير Full Stack",
            "علم البيانات",
            "تطوير تطبيقات الموبايل",
            "DevOps"
          ],
          correctAnswer: "Full Stack Development"
        },
        {
          id: "ind-4",
          type: "text" as const,
          question: "Name three major tech companies operating in Egypt:",
          questionAr: "اذكر ثلاث شركات تكنولوجيا كبرى تعمل في مصر:",
          hint: "Think about both international and local companies"
        },
        {
          id: "ind-5",
          type: "multiple-choice" as const,
          question: "What is the average entry-level software developer salary in Cairo (EGP)?",
          questionAr: "ما هو متوسط راتب مطور برامج مبتدئ في القاهرة (جنيه مصري)؟",
          options: [
            "5,000 - 8,000 EGP",
            "8,000 - 12,000 EGP",
            "12,000 - 18,000 EGP",
            "18,000 - 25,000 EGP"
          ],
          correctAnswer: "12,000 - 18,000 EGP"
        }
      ]
    }
  ]
};
