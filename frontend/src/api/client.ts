import type { CompareRequest, CompareResponse, OptionsResponse } from "./types";

export type ApiErrorKind = "validation" | "business" | "server" | "network";

export interface FieldError {
  field: string;
  message: string;
}

export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly code?: string;
  readonly fieldErrors: FieldError[];

  constructor(
    kind: ApiErrorKind,
    message: string,
    options: { code?: string; fieldErrors?: FieldError[] } = {},
  ) {
    super(message);
    this.name = "ApiError";
    this.kind = kind;
    this.code = options.code;
    this.fieldErrors = options.fieldErrors ?? [];
  }
}

const baseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

function parseValidation(detail: unknown[]): FieldError[] {
  return detail.map((item) => {
    const entry = item as { loc?: unknown[]; msg?: string };
    const path = (entry.loc ?? []).filter((p) => p !== "body").map(String);
    return { field: path.join("."), message: entry.msg ?? "" };
  });
}

async function toApiError(response: Response): Promise<ApiError> {
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  const data = body as {
    detail?: unknown;
    error?: { code?: string; message?: string };
  } | null;

  if (data && Array.isArray(data.detail)) {
    return new ApiError("validation", "הנתונים שהוזנו אינם תקינים", {
      fieldErrors: parseValidation(data.detail),
    });
  }
  if (data?.error?.message && response.status < 500) {
    return new ApiError("business", data.error.message, {
      code: data.error.code,
    });
  }
  return new ApiError("server", "אירעה שגיאה בשרת. נסו שוב מאוחר יותר", {
    code: data?.error?.code,
  });
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, init);
  } catch {
    throw new ApiError("network", "לא ניתן להתחבר לשרת. בדקו שהשרת פועל ונסו שוב");
  }
  if (!response.ok) {
    throw await toApiError(response);
  }
  return (await response.json()) as T;
}

export function getOptions(signal?: AbortSignal): Promise<OptionsResponse> {
  return request<OptionsResponse>("/api/v1/options", { signal });
}

export function compareScenarios(
  payload: CompareRequest,
  signal?: AbortSignal,
): Promise<CompareResponse> {
  return request<CompareResponse>("/api/v1/scenarios/compare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });
}
