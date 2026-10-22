import { NextRequest } from "next/server";

const BACKEND_URL = process.env.BACKEND_API_URL ?? "http://127.0.0.1:8000";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

async function proxyRequest(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;

  // Forward frontend /api/* requests to FastAPI /api/v1/*
  const targetUrl = new URL(
    `/api/v1/${path.map(encodeURIComponent).join("/")}`,
    BACKEND_URL,
  );

  targetUrl.search = request.nextUrl.search;

  const headers = new Headers();
  const contentType = request.headers.get("content-type");

  if (contentType) {
    headers.set("content-type", contentType);
  }

  try {
    const isReadOnlyRequest =
      request.method === "GET" || request.method === "HEAD";

    // Preserve the original binary data for multipart uploads.
    const body = isReadOnlyRequest
      ? undefined
      : contentType?.includes("multipart/form-data")
        ? await request.arrayBuffer()
        : await request.text();

    const response = await fetch(targetUrl, {
      method: request.method,
      headers,
      body,
      cache: "no-store",
    });

    const responseHeaders = new Headers();
    const responseContentType = response.headers.get("content-type");

    if (responseContentType) {
      responseHeaders.set("content-type", responseContentType);
    }

    return new Response(response.body, {
      status: response.status,
      headers: responseHeaders,
    });
  } catch (error) {
    console.error("Backend proxy request failed:", error);

    return Response.json(
      {
        detail:
          "Could not connect to the backend. Check the backend URL and availability.",
      },
      { status: 502 },
    );
  }
}

export const GET = proxyRequest;
export const POST = proxyRequest;
