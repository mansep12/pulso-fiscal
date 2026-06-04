import "server-only";

import { createClient } from "@supabase/supabase-js";

/**
 * Cliente publico de servidor. Usa anon key y respeta los permisos/RLS de Supabase.
 * Solo usar en Server Components o Route Handlers.
 */
export function createServerClient() {
  const supabaseUrl = process.env.SUPABASE_URL;
  if (!supabaseUrl || supabaseUrl === "REEMPLAZAR") {
    throw new Error(
      "SUPABASE_URL no configurada. Agrega la URL en web/.env.local.",
    );
  }

  const anonKey = process.env.SUPABASE_ANON_KEY;
  if (!anonKey || anonKey === "REEMPLAZAR") {
    throw new Error(
      "SUPABASE_ANON_KEY no configurada. Agrega tu anon key en web/.env.local.",
    );
  }

  return createClient(supabaseUrl, anonKey, {
    auth: { persistSession: false },
  });
}
