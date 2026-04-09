import './App.css'
import vtPantryLogo from './assets/VTPantry.png'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import AddItem from './AddItem.jsx';

function NavBar() {
  return (
    <nav className="navbar">
      <Link to="/"><img src={vtPantryLogo} style={{ height: "60px" }} /></Link>
      <Link to="/AddItem">Add Item</Link>

    </nav>
  )
}

function Home() {
  return (
    <>
      <NavBar />
      <h1>Welcome Home!</h1>
    </>
  );
}

function App() {
  return (
    <>
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
      </Router>

    </>
  )
}

export default App