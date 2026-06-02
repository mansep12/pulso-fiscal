import { createClient } from "@supabase/supabase-js";

/**
 * Cliente de servidor. Usa la secret key para saltarse RLS.
 * Solo usar en Server Components o Route Handlers, nunca en el browser.
 */
export function createServerClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  if (!supabaseUrl || supabaseUrl === "REEMPLAZAR") {
    throw new Error(
      "NEXT_PUBLIC_SUPABASE_URL no configurada. Agrega la URL en web/.env.local.",
    );
  }

  const secretKey = process.env.SUPABASE_SECRET_KEY;
  if (!secretKey || secretKey === "REEMPLAZAR") {
    throw new Error(
      "SUPABASE_SECRET_KEY no configurada. Agrega tu secret key en web/.env.local.",
    );
  }
  return createClient(supabaseUrl, secretKey, {
    auth: { persistSession: false },
  });
}
