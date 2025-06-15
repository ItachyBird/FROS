import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlane } from '@fortawesome/free-solid-svg-icons';
import { FaGithub, FaLinkedin } from "react-icons/fa";


import team1 from "../assets/soumyadip.jpg";
import team2 from "../assets/sayma.jpg";
import team3 from "../assets/naru.jpeg";
import team4 from "../assets/ritu.jpeg";

export default function Overlay({ navigate }) {
const members = [
  { name: "Soumyadip", img: team1, github: "https://github.com/ItachyBird", linkedin: "https://www.linkedin.com/in/soumyadip-debnath-04459a231/" },
  { name: "Piyali", img: team2, github: "https://github.com/Mukherjeepiyali", linkedin: "https://www.linkedin.com/in/piyali-mukherjee-906049239/" },
  { name: "Sreejan", img: team3, github: "https://github.com/XronTrix10", linkedin: "https://in.linkedin.com/in/sreejan-naru-472195237" },
  { name: "Rituraj", img: team4, github: "https://github.com/RiturajDebnath", linkedin: "https://www.linkedin.com/in/rituraj-debnath-2b5a2b35a/" },
];

  const handleClick = () => {
    navigate("/flightmainpage");
  };

  return (
    <>
      {/* Section 1 - Hero */}
      <div className="fixed w-screen h-screen top-0 flex items-end justify-center z-10 pb-10 bg-transparent no-scrollbar">
        <div className="text-center max-w-xl px-4 text-[#c9c7ba]">
          <h1 className="text-5xl font-bold mb-4" style={{ fontFamily: "'Savate', sans-serif" }}>
            Intelligent Flight Simulation Powered by AI Optimization
          </h1>
          <p className="mb-6">
            Experience adaptive navigation using Ant Colony Optimization, Genetic Algorithms, and Proximal Policy Optimization.
          </p>
          <div className="space-x-4">
            <button
              className="w-16 h-16 rounded-full bg-[#c9c7ba] text-xl text-black font-bold shadow-[0_0_12px_#c9c7ba] hover:shadow-[0_0_20px_#c9c7ba] transition-all duration-300"
              onClick={handleClick}
            >
              <FontAwesomeIcon icon={faPlane} className="text-xl text-[#29292b]" />
            </button>
          </div>
        </div>
      </div>

      {/* Section 2 - About */}
   <div className="fixed w-screen h-screen top-[100vh] flex items-center justify-start z-10 pl-10 bg-transparent no-scrollbar">
  <div className="max-w-xl text-left px-6 text-[#e0dfd6] space-y-4">
    <h1 className="text-4xl font-bold text-white mb-2 underline underline-offset-4 decoration-[#facc15]">
      Why This Simulation?
    </h1>
    <p className="text-lg leading-relaxed">
      In real-world aviation, route planning is a <span className="font-semibold italic">high-stakes, complex task</span> involving dynamic weather, fuel limits, no-fly zones, and live air traffic.
    </p>
    <p className="text-lg leading-relaxed">
      Our simulation leverages <span className="font-bold text-[#93c5fd]">AI-powered optimization</span> using 
      <span className="font-semibold italic text-[#86efac]"> ACO</span>, 
      <span className="font-semibold italic text-[#f9a8d4]"> GA</span>, and 
      <span className="font-semibold italic text-[#fca5a5]"> PPO</span> to outperform traditional tools like FMS or dispatcher planning.
    </p>
    <p className="text-lg leading-relaxed">
      It simulates <span className="font-bold text-[#fcd34d]">real-time rerouting</span>, live weather adaptation, and safety-first decisions—something rarely possible in current static systems.
    </p>
    <p className="text-lg leading-relaxed">
      With <span className="italic">learning agents</span> and intelligent feedback loops, this system gets <span className="font-bold">smarter over time</span>, making it ideal for 
      future autonomous aviation systems.
    </p>
    <p className="text-lg leading-relaxed text-gray-300">
      ✈️ Inspired by real-world <span className="font-medium">ATC networks, drone pathing systems, and aerospace AI research</span>—this simulation represents the 
      next leap in intelligent air route generation.
    </p>
  </div>
</div>


      {/* Section 3 - Tech Stack */}
     <div className="fixed w-screen h-screen top-[200vh] flex items-start justify-end z-10 pt-20 pr-10 bg-transparent no-scrollbar">
  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl text-[#c9c7ba]">
    {[
      {
        title: "Ant Colony Optimization (ACO)",
        description:
          "ACO is inspired by how ants find the shortest path to food using pheromone trails. In flight routing, it mimics swarm behavior to discover optimal and adaptive routes through complex, changing airspaces—efficiently avoiding weather hazards or closed zones."
      },
      {
        title: "Genetic Algorithm (GA)",
        description:
          "GA simulates biological evolution to improve route planning. It uses processes like selection, crossover, and mutation to iteratively evolve flight paths that optimize cost, time, and safety—ideal for balancing multiple constraints across long-haul flights."
      },
      {
        title: "Proximal Policy Optimization (PPO)",
        description:
          "PPO is a reinforcement learning method that continuously learns and improves decisions in real-time. It adapts to sudden weather changes, air traffic, and emergencies—allowing dynamic rerouting and smarter planning in unpredictable scenarios."
      }
    ].map(({ title, description }) => (
      <div
        key={title}
        className="p-6 rounded-xl bg-[#1f1f21] transition duration-300 hover:animate-bounce-custom shadow-md shadow-black/20"
      >
        <h2 className="text-xl font-bold mb-3 text-white">{title}</h2>
        <p className="text-sm leading-relaxed text-gray-300">{description}</p>
      </div>
    ))}
  </div>
</div>


      {/* Section 4 - Demo Preview */}
<div className="fixed w-screen h-screen top-[300vh] flex items-center justify-center z-10 bg-transparent no-scrollbar">
  <div className="text-center max-w-xl px-4 text-[#c9c7ba]">
    <h1 className="text-3xl font-bold mb-4">Demo / Simulation Preview</h1>
    <p className="mb-4">
      See the AI in action with live simulations or pre-recorded scenarios showing intelligent flight decision-making.
    </p>
<div className="space-x-4">
  <a
    href="#"
    target="_blank"
    rel="noopener noreferrer"
    className="inline-block"
  >
    <button
      className="btn transition duration-200 hover:underline hover:text-yellow-300 hover:shadow-[0_0_10px_2px_rgba(255,255,120,0.7)] hover:cursor-pointer"
    >
      Launch Simulation
    </button>
  </a>
  <a
    href="#"
    target="_blank"
    rel="noopener noreferrer"
    className="inline-block"
  >
    <button
      className="btn transition duration-200 hover:underline hover:text-yellow-300 hover:shadow-[0_0_10px_2px_rgba(255,255,120,0.7)] hover:cursor-pointer"
    >
      Download Dataset
    </button>
  </a>
</div>
  </div>
</div>

      {/* Section 5 - Team */}
      <div className="fixed w-screen h-screen top-[400vh] z-10 flex items-center justify-center bg-transparent no-scrollbar">
        <div className="w-full max-w-5xl grid grid-cols-2 grid-rows-2 gap-10 p-8">
          {members.map((member, i) => (
            <div
              key={member.name}
              className={`flex ${i % 2 === 0 ? "justify-start" : "justify-end"}`}
            >
              <div
                className="bg-[#1f1f21] rounded-xl shadow-lg p-6 flex flex-col items-center text-[#c9c7ba] space-y-2
                           transition duration-300 hover:animate-bounce-custom
                           shadow-[0_0_12px_#c9c7ba] hover:shadow-[0_0_20px_#c9c7ba]"
              >
                <img
                  src={member.img}
                  alt={member.name}
                  className="w-24 h-24 rounded-full object-cover mb-2 border-4 border-[#c9c7ba] shadow-[0_0_12px_#c9c7ba]"
                />
                <h2 className="text-xl font-bold">{member.name}</h2>
                <div className="flex flex-row items-center space-x-3 mt-1">
                  <a href={member.github} target="_blank" rel="noopener noreferrer" className="hover:text-white transition">
                    <FaGithub size={22} />
                  </a>
                  <a href={member.linkedin} target="_blank" rel="noopener noreferrer" className="hover:text-[#0e76a8] transition">
                    <FaLinkedin size={22} />
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
