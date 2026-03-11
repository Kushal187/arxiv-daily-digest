export const RESEARCH_AREAS = [
  {
    slug: "nlp",
    label: "NLP",
    description: "Language models, reasoning, generation, and language-centric systems."
  },
  {
    slug: "computer-vision",
    label: "Computer Vision",
    description: "Recognition, detection, segmentation, and core visual understanding."
  },
  {
    slug: "vision-3d",
    label: "3D Vision",
    description: "Reconstruction, 3D perception, scene understanding, and geometry."
  },
  {
    slug: "multimodal",
    label: "Multimodal",
    description: "Vision-language, video-language, and cross-modal reasoning."
  },
  {
    slug: "information-retrieval",
    label: "Information Retrieval / Search",
    description: "Search ranking, retrieval systems, recommenders, and relevance."
  },
  {
    slug: "reinforcement-learning",
    label: "Reinforcement Learning",
    description: "Policy learning, offline RL, exploration, and sequential decisions."
  },
  {
    slug: "robotics",
    label: "Robotics",
    description: "Embodied agents, manipulation, control, and robot learning."
  },
  {
    slug: "speech-audio",
    label: "Speech / Audio",
    description: "ASR, TTS, speech-language modeling, and audio generation."
  },
  {
    slug: "graph-ml",
    label: "Graph ML",
    description: "Graph neural networks, graph transformers, and structured learning."
  },
  {
    slug: "theoretical-ml",
    label: "Theoretical ML",
    description: "Learning theory, optimization theory, scaling laws, and guarantees."
  },
  {
    slug: "interpretability",
    label: "Interpretability",
    description: "Mechanistic interpretability, probing, saliency, and concept analysis."
  },
  {
    slug: "training-systems-efficiency",
    label: "Training / Systems / Efficiency",
    description: "Efficient training, quantization, distillation, and inference systems."
  },
  {
    slug: "safety-alignment",
    label: "Safety / Alignment",
    description: "Alignment, red teaming, safeguards, and model behavior shaping."
  },
  {
    slug: "medical-bio-ml",
    label: "Medical / Bio ML",
    description: "Clinical, biological, and medical machine learning applications."
  }
] as const;

export type ResearchAreaSlug = (typeof RESEARCH_AREAS)[number]["slug"];

export const SUBTOPIC_TAXONOMY = [
  { slug: "retrieval-rag", label: "Retrieval / RAG", areaSlug: "nlp" },
  { slug: "llm-evaluation", label: "LLM Evaluation", areaSlug: "nlp" },
  { slug: "agent-systems", label: "Agent Systems", areaSlug: "nlp" },
  { slug: "reasoning-planning", label: "Reasoning / Planning", areaSlug: "nlp" },
  { slug: "pure-cv", label: "Pure Computer Vision", areaSlug: "computer-vision" },
  { slug: "diffusion-generative", label: "Diffusion / Generative Vision", areaSlug: "computer-vision" },
  { slug: "reconstruction-3d", label: "3D Reconstruction", areaSlug: "vision-3d" },
  { slug: "scene-understanding-3d", label: "3D Scene Understanding", areaSlug: "vision-3d" },
  { slug: "multimodal-vlm", label: "Vision-Language / Multimodal", areaSlug: "multimodal" },
  { slug: "information-retrieval", label: "Information Retrieval", areaSlug: "information-retrieval" },
  { slug: "graph-learning", label: "Graph Learning", areaSlug: "graph-ml" },
  { slug: "reinforcement-learning", label: "Reinforcement Learning", areaSlug: "reinforcement-learning" },
  { slug: "robotics", label: "Robotics", areaSlug: "robotics" },
  { slug: "speech-audio", label: "Speech / Audio", areaSlug: "speech-audio" },
  { slug: "learning-theory", label: "Learning Theory", areaSlug: "theoretical-ml" },
  { slug: "mechanistic-interpretability", label: "Mechanistic Interpretability", areaSlug: "interpretability" },
  { slug: "training-efficiency", label: "Training Efficiency", areaSlug: "training-systems-efficiency" },
  { slug: "safety-alignment", label: "Safety / Alignment", areaSlug: "safety-alignment" },
  { slug: "medical-imaging", label: "Medical Imaging", areaSlug: "medical-bio-ml" }
] as const;

export type SubtopicSlug = (typeof SUBTOPIC_TAXONOMY)[number]["slug"];
export type TopicSlug = SubtopicSlug;

export const DEFAULT_ARXIV_CATEGORIES = [
  "cs.AI",
  "cs.LG",
  "cs.CL",
  "cs.CV",
  "cs.IR",
  "stat.ML",
  "cs.RO",
  "eess.AS"
] as const;

const AREA_LABELS = new Map<string, string>(RESEARCH_AREAS.map((area) => [area.slug, area.label]));
const SUBTOPIC_LABELS = new Map<string, string>(SUBTOPIC_TAXONOMY.map((topic) => [topic.slug, topic.label]));
const SUBTOPIC_AREA_MAP = new Map<string, ResearchAreaSlug>(
  SUBTOPIC_TAXONOMY.map((topic) => [topic.slug, topic.areaSlug])
);

const LEGACY_TOPIC_AREA_MAP: Record<string, ResearchAreaSlug> = {
  "retrieval-rag": "nlp",
  "llm-evaluation": "nlp",
  "agent-systems": "nlp",
  "multimodal-vlm": "multimodal",
  "diffusion-generative": "computer-vision",
  "graph-learning": "graph-ml",
  "medical-imaging": "medical-bio-ml",
  "reinforcement-learning": "reinforcement-learning",
  robotics: "robotics",
  "speech-audio": "speech-audio",
  "information-retrieval": "information-retrieval",
  "reasoning-planning": "nlp",
  "training-efficiency": "training-systems-efficiency",
  "safety-alignment": "safety-alignment"
};

const RESEARCH_AREA_SET = new Set<string>(RESEARCH_AREAS.map((area) => area.slug));

export function isResearchAreaSlug(value: string): value is ResearchAreaSlug {
  return RESEARCH_AREA_SET.has(value);
}

export function getAreaLabel(slug: string): string {
  return AREA_LABELS.get(slug) ?? slug;
}

export function getTopicLabel(slug: string): string {
  return SUBTOPIC_LABELS.get(slug) ?? AREA_LABELS.get(slug) ?? slug;
}

export function legacyTopicToArea(slug: string): ResearchAreaSlug | null {
  return LEGACY_TOPIC_AREA_MAP[slug] ?? null;
}

export function subtopicToArea(slug: string): ResearchAreaSlug | null {
  return SUBTOPIC_AREA_MAP.get(slug) ?? null;
}

export function normalizeAreaSlugs(values: string[]): ResearchAreaSlug[] {
  const normalized: ResearchAreaSlug[] = [];
  const seen = new Set<ResearchAreaSlug>();

  for (const value of values) {
    const slug = isResearchAreaSlug(value) ? value : legacyTopicToArea(value);
    if (!slug || seen.has(slug)) {
      continue;
    }

    seen.add(slug);
    normalized.push(slug);
  }

  return normalized;
}
