import './App.css'
import vtPantryLogo from './assets/VTPantry.png'

function App() {

  return (
    <>
      <NavBar />
    </>
  )
}


function NavBar() {

  return (
    <>
      <nav className="navbar">
        <a href="/index.html"><img src={vtPantryLogo} style={{ height: "60px" }} /></a>
        <a href="/index.html">Inventory</a>
      </nav>

    </>
  )
}



export default App
