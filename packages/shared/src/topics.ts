export const TOPIC_TAXONOMY = [
  { slug: "retrieval-rag", label: "Retrieval / RAG", description: "Dense retrieval, reranking, retrieval-augmented generation, indexing pipelines." },
  { slug: "llm-evaluation", label: "LLM Evaluation", description: "Benchmarks, judge models, evaluation methodology, robustness tests." },
  { slug: "agent-systems", label: "Agent Systems", description: "Tool use, task execution, multi-agent systems, autonomous workflows." },
  { slug: "multimodal-vlm", label: "Multimodal / VLM", description: "Vision-language models, image-text reasoning, multimodal fusion." },
  { slug: "diffusion-generative", label: "Diffusion / Generative", description: "Diffusion models, score matching, generative modeling, synthesis." },
  { slug: "graph-learning", label: "Graph Learning", description: "Graph neural networks, structured reasoning, graph retrieval." },
  { slug: "medical-imaging", label: "Medical Imaging", description: "Clinical imaging, diagnosis support, radiology and pathology ML." },
  { slug: "reinforcement-learning", label: "Reinforcement Learning", description: "Policy learning, offline RL, decision making under uncertainty." },
  { slug: "robotics", label: "Robotics", description: "Embodied control, robot learning, planning, manipulation, locomotion." },
  { slug: "speech-audio", label: "Speech / Audio", description: "Speech recognition, audio generation, speech-language modeling." },
  { slug: "information-retrieval", label: "Information Retrieval", description: "Search ranking, retrieval evaluation, recommender retrieval layers." },
  { slug: "reasoning-planning", label: "Reasoning / Planning", description: "Structured reasoning, search, decomposition, long-horizon planning." },
  { slug: "training-efficiency", label: "Training Efficiency", description: "Quantization, distillation, efficient finetuning, systems efficiency." },
  { slug: "safety-alignment", label: "Safety / Alignment", description: "Alignment, policy shaping, red teaming, safeguards, misuse prevention." }
] as const;

export type TopicSlug = (typeof TOPIC_TAXONOMY)[number]["slug"];

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
