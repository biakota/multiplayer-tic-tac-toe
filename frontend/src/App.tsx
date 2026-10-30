import { useEffect, useRef, useState } from "react";

type Game = { room_code:string; board:(string|null)[][]; players:Record<string,string|null>; current_turn:string; status:string; winner:string|null; winning_line:number[][]|null; rematch_votes:string[]; disconnected:string[] };
const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
const WS = API.replace(/^http/, "ws");
const savedId = () => sessionStorage.getItem("ttt-player-id");

export default function App() {
  const [game,setGame] = useState<Game|null>(null);
  const [playerId,setPlayerId] = useState<string|null>(savedId());
  const [symbol,setSymbol] = useState<string|null>(sessionStorage.getItem("ttt-symbol"));
  const [roomInput,setRoomInput] = useState("");
  const [socketStatus,setSocketStatus] = useState("offline");
  const [error,setError] = useState("");
  const [copied,setCopied] = useState(false);
  const socket = useRef<WebSocket|null>(null);

  async function createRoom() {
    setError("");
    try {
      const response = await fetch(`${API}/api/rooms`,{method:"POST"});
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not create room");
      enterGame(data);
    } catch(e) { setError(e instanceof Error ? e.message : "Network error"); }
  }
  async function joinRoom() {
    setError("");
    try {
      const id = playerId || crypto.randomUUID() + crypto.randomUUID();
      const response = await fetch(`${API}/api/rooms/${roomInput.trim().toUpperCase()}/join`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({player_id:id})});
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not join room");
      enterGame(data);
    } catch(e) { setError(e instanceof Error ? e.message : "Network error"); }
  }
  function enterGame(data:any) {
    sessionStorage.setItem("ttt-player-id",data.player_id);
    sessionStorage.setItem("ttt-symbol",data.symbol);
    setPlayerId(data.player_id); setSymbol(data.symbol); setGame(data.game);
  }
  useEffect(() => {
    if (!game || !playerId) return;
    const ws = new WebSocket(`${WS}/ws/${game.room_code}/${playerId}`);
    socket.current = ws;
    ws.onopen = () => setSocketStatus("connected");
    ws.onclose = () => setSocketStatus("offline");
    ws.onerror = () => setSocketStatus("offline");
    ws.onmessage = event => {
      const msg = JSON.parse(event.data);
      if (msg.type === "state") setGame(msg.game);
      if (msg.type === "player_disconnected") { setGame(msg.game); setError("Your opponent disconnected. They can reconnect using their session."); }
      if (msg.type === "error") setError(msg.message);
    };
    return () => { ws.close(); socket.current = null; };
  },[game?.room_code,playerId]);
  function send(payload:object) {
    if (socket.current?.readyState === WebSocket.OPEN) { setError(""); socket.current.send(JSON.stringify(payload)); }
    else setError("Connection is not ready. Please wait a moment.");
  }
  async function copyCode() {
    if (!game) return;
    await navigator.clipboard.writeText(game.room_code);
    setCopied(true); window.setTimeout(()=>setCopied(false),1500);
  }
  function leave() { socket.current?.close(); setGame(null); setSymbol(null); setError(""); sessionStorage.removeItem("ttt-player-id"); sessionStorage.removeItem("ttt-symbol"); setPlayerId(null); }
  const myTurn = !!game && game.current_turn === symbol && game.status === "PLAYING";
  const winnerText = game?.winner ? `${game.winner === symbol ? "You won!" : "Your opponent won!"}` : "It's a draw!";
  const line = game?.winning_line?.map(([r,c])=>`${r}-${c}`) || [];

  return <main className="shell">
    <nav className="nav"><a className="brand" href="#"><span className="brand-icon">✳</span> GRIDLOCK</a><span className={`connection ${socketStatus}`}><i/> {socketStatus === "connected" ? "LIVE CONNECTION" : "NOT CONNECTED"}</span></nav>
    {!game ? <section className="hero">
      <div className="eyebrow"><span/> REAL-TIME MULTIPLAYER</div><h1>One grid.<br/><em>Two minds.</em></h1>
      <p className="intro">A little friendly competition, wherever you are. Create a room or join a friend to play live.</p>
      <div className="entry-card"><div className="card-title">START A NEW MATCH</div><button className="primary" onClick={createRoom}>Create a room <span>↗</span></button><div className="or"><span/> OR JOIN A FRIEND <span/></div><label htmlFor="room">ROOM CODE</label><div className="join-row"><input id="room" maxLength={6} placeholder="ENTER CODE" value={roomInput} onChange={e=>setRoomInput(e.target.value.toUpperCase())}/><button disabled={roomInput.trim().length!==6} onClick={joinRoom}>Join</button></div></div>
      <div className="rules"><span>✦</span> First to connect three marks wins. X always starts.</div>
      {error && <div className="error">{error}</div>}
    </section> : <section className="game-wrap">
      <div className="game-top"><button className="back" onClick={leave}>← Leave game</button><div className="room-badge">ROOM <b>{game.room_code}</b><button onClick={copyCode} aria-label="Copy room code">{copied?"✓":"▢"}</button></div></div>
      <div className="game-heading"><div className="eyebrow"><span/> {game.status === "WAITING" ? "ROOM OPEN" : game.status === "FINISHED" ? "MATCH COMPLETE" : "MATCH IN PROGRESS"}</div><h2>{game.status==="WAITING"?"Waiting for a challenger":game.status==="FINISHED"?winnerText:myTurn?"Your move.":"Opponent's move."}</h2><p>{game.status==="WAITING"?"Share the room code with a friend to begin.":game.status==="FINISHED"?"Ready for another round?":myTurn?"Place your mark on the board.":"Hang tight — they're thinking."}</p></div>
      <div className="players"><div className={`player ${symbol==="X"?"active":""}`}><span className="mark x">×</span><div><b>PLAYER X</b><small>{game.players.X===playerId?"YOU":"OPPONENT"}</small></div><strong>{symbol==="X"?"YOU":"X"}</strong></div><div className={`player ${symbol==="O"?"active":""}`}><span className="mark o">○</span><div><b>PLAYER O</b><small>{game.players.O===playerId?"YOU":game.players.O?"OPPONENT":"WAITING..."}</small></div><strong>{symbol==="O"?"YOU":"O"}</strong></div></div>
      <div className="board" role="grid" aria-label="Tic Tac Toe board">{game.board.map((row,r)=>row.map((cell,c)=><button key={`${r}-${c}`} role="gridcell" aria-label={`Row ${r+1}, column ${c+1}${cell?`, ${cell}`:" empty"}`} className={`cell ${cell==="X"?"x":cell==="O"?"o":""} ${line.includes(`${r}-${c}`)?"winning":""}`} disabled={!myTurn||!!cell} onClick={()=>send({type:"make_move",row:r,col:c})}>{cell==="X"?"×":cell==="O"?"○":""}</button>))}</div>
      {game.status==="WAITING" && <div className="waiting-note"><span className="pulse"/> Waiting for player O to join</div>}
      {game.status==="FINISHED" && <button className="primary rematch" onClick={()=>send({type:"request_rematch"})}>{game.rematch_votes.includes(playerId||"")?"Waiting for opponent…":"↻ Request rematch"}</button>}
      {game.status==="PLAYING" && <div className="turn-note">{myTurn?"● YOUR TURN":"◌ OPPONENT'S TURN"}</div>}
      {error && <div className="error">{error}</div>}
      <div className="game-foot">BEST OF ONE <span>•</span> CLASSIC RULES <span>•</span> NO MERCY</div>
    </section>}
    <footer>BUILT FOR FRIENDLY RIVALRIES <span>© 2026 GRIDLOCK</span></footer>
  </main>;
}
