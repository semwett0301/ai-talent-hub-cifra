import {
  BrowserRouter,
  Navigate,
  NavLink,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";
import { useEffect, useState } from "react";
import {
  Radio,
  Inbox,
  Scale,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { NewsPage } from "@/pages/NewsPage";
import { NpaPage } from "@/pages/NpaPage";
import { SourcesPage } from "@/pages/SourcesPage";
import "./App.css";

function App() {
  const [collapsed, setCollapsed] = useState(false);
  return (
    <BrowserRouter>
      <ScrollToTop />
      <div className={`app-shell ${collapsed ? "is-collapsed" : ""}`}>
        <header className="masthead">
          <div>
            <p className="eyebrow">AI-ЦЕНТР · GS LABS</p>
            <h1>Мониторинг без шума</h1>
          </div>
          <div className="brand">
            <span className="demo-label">Демо · mock data</span>
            <span className="avatar purple">ВБ</span>
            <span>GS LABS</span>
          </div>
        </header>
        <div className="workspace">
          <aside className="sidebar panel">
            <nav aria-label="Основная навигация">
              {[
                { to: "/news", title: "Входящие", icon: Inbox },
                { to: "/npa", title: "НПА", icon: Scale },
                { to: "/sources", title: "Источники", icon: Radio },
              ].map(({ to, title, icon: Icon }) => (
                <NavLink key={to} to={to} title={title}>
                  <Icon size={19} />
                  {!collapsed && title}
                </NavLink>
              ))}
            </nav>
            <div className="sidebar-bottom">
              <Button
                variant="ghost"
                onClick={() => setCollapsed(!collapsed)}
                aria-label={collapsed ? "Развернуть меню" : "Свернуть меню"}
              >
                {collapsed ? <ChevronRight /> : <ChevronLeft />}
                {!collapsed && "Свернуть"}
              </Button>
            </div>
          </aside>
          <main>
            <Routes>
              <Route path="/news" element={<NewsPage />} />
              <Route path="/npa" element={<NpaPage />} />
              <Route path="/sources" element={<SourcesPage />} />
              <Route path="*" element={<Navigate to="/news" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}
export default App;

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}
