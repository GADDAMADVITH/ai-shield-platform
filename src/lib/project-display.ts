import type { LucideIcon } from "lucide-react";
import { Bot, Braces, MessageSquare, Workflow } from "lucide-react";
import { APPLICATION_TYPES, type ApplicationType } from "@/components/create-project-dialog";

export type ProjectTone = "success" | "warning" | "danger" | "info" | "muted";

export function scoreTone(score: number): ProjectTone {
  if (score >= 90) return "success";
  if (score >= 80) return "warning";
  return "danger";
}

export function iconForType(type: ApplicationType | string): LucideIcon {
  if (type.includes("RAG") || type.includes("Document")) return Bot;
  if (type.includes("Coding") || type.includes("Agent") || type.includes("Autonomous")) return Workflow;
  if (
    type.includes("Custom") ||
    type.includes("Analytics") ||
    type.includes("Resume") ||
    type.includes("Embeddings")
  )
    return Braces;
  return MessageSquare;
}

export function inferApplicationType(type: string): ApplicationType {
  const normalized = type.toLowerCase();
  if (normalized.includes("rag") || normalized.includes("document")) return "RAG / Document Q&A";
  if (normalized.includes("coding") || normalized.includes("copilot") || normalized.includes("agent"))
    return "AI Coding Assistant";
  if (normalized.includes("support") || normalized.includes("customer"))
    return "AI Customer Support Assistant";
  if (normalized.includes("chat") || normalized.includes("voice")) return "AI Chatbot";
  if (normalized.includes("embed")) return "Custom AI Application";
  const match = APPLICATION_TYPES.find((t) => t === type);
  return match ?? "Custom AI Application";
}
