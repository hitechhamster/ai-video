import { NavLink, Route, Routes } from "react-router-dom";
import TemplateGallery from "./pages/TemplateGallery";
import ProjectList from "./pages/ProjectList";
import NewProject from "./pages/NewProject";
import StyleManager from "./pages/StyleManager";
import EffectPresetManager from "./pages/EffectPresetManager";
import MusicManager from "./pages/MusicManager";
import ProjectResult from "./pages/ProjectResult";

function App() {
  return (
    <>
      <header className="app-header">
        <div className="app-header-inner">
          <div className="brand">
            <span className="brand-mark">火</span>
            <h1>AI火柴人</h1>
          </div>
          <nav>
            <NavLink to="/" end>
              模板
            </NavLink>
            <NavLink to="/new">自定义生成</NavLink>
            <NavLink to="/projects">我的项目</NavLink>
            <NavLink to="/styles">画风</NavLink>
            <NavLink to="/effects">效果预设</NavLink>
            <NavLink to="/music">音乐</NavLink>
          </nav>
        </div>
      </header>
      <div className="app">
        <main className="app-main">
          <Routes>
            <Route path="/" element={<TemplateGallery />} />
            <Route path="/new" element={<NewProject />} />
            <Route path="/projects" element={<ProjectList />} />
            <Route path="/styles" element={<StyleManager />} />
            <Route path="/effects" element={<EffectPresetManager />} />
            <Route path="/music" element={<MusicManager />} />
            <Route path="/projects/:id" element={<ProjectResult />} />
          </Routes>
        </main>
      </div>
    </>
  );
}

export default App;
