// Supabase Edge Function: keep-alive
// Prevents Supabase Free Tier projects from pausing after 7 days of inactivity.
// Deployed to: https://<PROJECT_REF>.supabase.co/functions/v1/keep-alive

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

Deno.serve(async (req: Request) => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response("ok", {
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
      },
    });
  }

  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Content-Type": "application/json",
  };

  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL") ?? "";
    const supabaseKey =
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ??
      Deno.env.get("SUPABASE_ANON_KEY") ??
      "";

    if (!supabaseUrl || !supabaseKey) {
      return new Response(
        JSON.stringify({
          status: "error",
          message: "SUPABASE_URL or SUPABASE_ANON_KEY is not configured.",
        }),
        { status: 500, headers: corsHeaders }
      );
    }

    const supabase = createClient(supabaseUrl, supabaseKey);

    // 1. Query the database to register active read traffic
    const { data, error, count } = await supabase
      .from("tweet_history")
      .select("id, tweet_id, created_at", { count: "exact" })
      .order("id", { ascending: false })
      .limit(1);

    const now = new Date().toISOString();

    if (error) {
      // If table doesn't exist yet, query schema metadata as fallback
      const { data: schemaData, error: schemaError } = await supabase
        .from("bot_replies")
        .select("id")
        .limit(1);

      return new Response(
        JSON.stringify({
          status: "alive",
          notice: "Database pinged via fallback query.",
          timestamp: now,
          error: error.message,
          schemaCheck: schemaError ? schemaError.message : "ok",
        }),
        { status: 200, headers: corsHeaders }
      );
    }

    return new Response(
      JSON.stringify({
        status: "alive",
        message: "Database pinged successfully. Inactivity pause timer reset.",
        timestamp: now,
        total_posts_logged: count,
        latest_post: data && data.length > 0 ? data[0] : null,
      }),
      { status: 200, headers: corsHeaders }
    );
  } catch (err: any) {
    return new Response(
      JSON.stringify({
        status: "error",
        message: err.message || "Unknown error during database keep-alive.",
      }),
      { status: 500, headers: corsHeaders }
    );
  }
});
