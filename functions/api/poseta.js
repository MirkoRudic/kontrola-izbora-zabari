// Brojač poseta: ukupno poseta i jedinstvenih posetilaca (anonimni ID iz pregledača, bez ličnih podataka).
const counts = async (db) => {
  const r = await db.prepare("SELECT COUNT(*) AS posete, COUNT(DISTINCT vid) AS jedinstvene FROM posete").first();
  return { posete: r?.posete ?? 0, jedinstvene: r?.jedinstvene ?? 0 };
};
const json = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { "content-type": "application/json", "cache-control": "no-store" } });

export async function onRequestPost({ request, env }) {
  let vid = "";
  try { vid = String((await request.json()).vid || ""); } catch (e) {}
  if (!/^[a-z0-9]{12,40}$/.test(vid)) return json({ error: "bad id" }, 400);
  await env.DB.prepare("INSERT INTO posete (vid) VALUES (?)").bind(vid).run();
  return json(await counts(env.DB));
}
export async function onRequestGet({ env }) {
  return json(await counts(env.DB));
}
