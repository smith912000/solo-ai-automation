import "./globals.css";

export const metadata = {
  title: "Command Center",
  description: "Operations dashboard for Solo AI Automation",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <main className="container">
          <header className="header">
            <h1>Command Center</h1>
            <nav className="nav">
              <a href="/">Dashboard</a>
              <a href="/pipeline">Pipeline</a>
              <a href="/agents">Agents</a>
              <a href="/approvals">Approvals</a>
              <a href="/analytics">Analytics</a>
            </nav>
          </header>
          {children}
        </main>
      </body>
    </html>
  );
}
