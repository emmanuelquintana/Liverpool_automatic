import { Clock3, LockKeyhole, Route, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string; next?: string }>;
}) {
  const { error, next = "/" } = await searchParams;
  return (
    <main className="login-shell">
      <section className="login-context" aria-labelledby="login-context-title">
        <div className="login-brand">
          <span className="brand-mark" aria-hidden="true">G</span>
          <span><strong>Goldval</strong><small>Operación Liverpool</small></span>
        </div>
        <div className="login-copy">
          <p className="eyebrow">Torre de seguimiento</p>
          <h1 id="login-context-title">Cada guía,<br />bajo vigilancia.</h1>
          <p>Pedidos, alertas y entregas reunidos en una sola vista operativa.</p>
        </div>
        <div className="route-line" aria-label="Flujo monitoreado: pedido, tránsito y entrega">
          <span><i aria-hidden="true" /> Pedido</span>
          <span><i aria-hidden="true" /> Tránsito</span>
          <span><i aria-hidden="true" /> Entrega</span>
        </div>
        <div className="login-monitor">
          <Clock3 aria-hidden="true" />
          <span><strong>Monitoreo automático</strong><small>Revisión diaria 06:00 · reintentos activos</small></span>
        </div>
      </section>

      <section className="login-entry" aria-labelledby="login-title">
        <div className="login-form-wrap">
          <div className="login-shield" aria-hidden="true"><ShieldCheck /></div>
          <p className="eyebrow">Acceso restringido</p>
          <h2 id="login-title">Entrar al centro de control</h2>
          <p className="login-intro">Usa las credenciales privadas de Goldval para continuar.</p>
          {error && (
            <p className="login-error" role="alert">
              {error === "config" ? "El acceso aún no está configurado." : "El usuario o la contraseña no coinciden."}
            </p>
          )}
          <form className="login-form" action="/api/login" method="post">
            <input type="hidden" name="next" value={next} />
            <label htmlFor="username">Usuario</label>
            <Input id="username" name="username" autoComplete="username" required autoFocus />
            <label htmlFor="password">Contraseña</label>
            <Input id="password" name="password" type="password" autoComplete="current-password" required />
            <Button type="submit">
              <LockKeyhole aria-hidden="true" /> Ingresar de forma segura
            </Button>
          </form>
          <p className="login-assurance"><Route aria-hidden="true" /> Sesión cifrada y válida por 12 horas.</p>
        </div>
      </section>
    </main>
  );
}
