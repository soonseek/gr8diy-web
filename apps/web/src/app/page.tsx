export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-center font-mono text-sm">
        <h1 className="text-4xl font-bold mb-4">Welcome to gr8diy web</h1>
        <p className="text-muted-foreground mb-8">
          Full-stack application with FastAPI + Next.js + Turborepo
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="border rounded-lg p-4">
            <h2 className="font-semibold mb-2">FastAPI</h2>
            <p className="text-sm text-muted-foreground">Backend API with SQLAlchemy 2.0</p>
          </div>
          <div className="border rounded-lg p-4">
            <h2 className="font-semibold mb-2">Next.js</h2>
            <p className="text-sm text-muted-foreground">Frontend with App Router</p>
          </div>
          <div className="border rounded-lg p-4">
            <h2 className="font-semibold mb-2">Turborepo</h2>
            <p className="text-sm text-muted-foreground">Monorepo with build caching</p>
          </div>
        </div>
      </div>
    </main>
  );
}
