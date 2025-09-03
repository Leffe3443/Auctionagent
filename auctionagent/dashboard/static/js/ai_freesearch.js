
// CSRF (Django standard)
function getCookie(name){
  const v = `; ${document.cookie}`;
  const p = v.split(`; ${name}=`);
  if (p.length === 2) return p.pop().split(';').shift();
}

const freesearchform = document.getElementById("aiFreeSearchForm");
const freesearchbtn  = document.getElementById("aiRunFreeSearchBtn");
const freesearch_output  = document.getElementById("aiFreeSearchResults");
const aithinkfreesearch = document.getElementById("ai-thinkingfreesearch");

freesearchform.addEventListener("submit", async (e) => {
  e.preventDefault(); // stop full reload

//   const object_type = document.getElementById("object_type").value.trim();
  const object_type = document.getElementById("object_type_freesearch").value;
  const userprompt_freesearch = document.getElementById("aiFreeSearchPrompt").value;

  console.log("Object type:", object_type)
  console.log("User prompt:", userprompt_freesearch)
  
  
  aithinkfreesearch.style.visibility = "visible";

  freesearchbtn.disabled = true;
  const freesearchbtntext_old = freesearchbtn.textContent;
  freesearchbtn.textContent = "Söker…";

  const url = `api/auction-agent/aifreesearch/?object_type=${encodeURIComponent(object_type)}&userprompt_freesearch=${encodeURIComponent(userprompt_freesearch)}`;

  try {    

    const res = await fetch(url, {
      method: "GET",
      // headers: {
      //   "X-CSRFToken": getCookie("csrftoken"),
      //   // "Content-Type": "application/json"
      // },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();    

    const md = data.response_ai_content || ""; // full Markdown from backend

    console.log("MD:", md)
    // Kick off the animation:
    renderAiWithTyping(freesearch_output, md);

    
    // const html = DOMPurify.sanitize(marked.parse(md, { breaks: true })); // convert + sanitize


    // freesearch_output.innerHTML = '';

    // // Time.sleep(3-4 sekunder)
    // // Animation that runs here "**Formulerar för läsbarheten**"

    // freesearch_output.innerHTML = `
    // <div class="card mb-3">
    //     <div class="card-body">
    //     ${html}
    //     </div>
    // </div>
    // `;
  } catch (err) {
    freesearch_output.innerHTML = `<div class="alert alert-danger">Fel: ${err.message || err}</div>`;
  } finally {
    freesearchbtn.disabled = false;
    freesearchbtn.textContent = freesearchbtntext_old;
    aithinkfreesearch.style.visibility = 'hidden';

  }

});


// to cancel overlapping runs if user clicks again
let aiWriteRunId = 0;

async function renderAiWithTyping(targetEl, mdText) {
  aiWriteRunId++;
  const runId = aiWriteRunId;

  // Card shell & target where we will type
  targetEl.innerHTML = `
    <div class="card mb-3">
      <div class="card-body">
        <div id="aiTypeTarget"></div>
      </div>
    </div>`;
  const typeTarget = document.getElementById("aiTypeTarget");

  // brief pre-roll; tweak to 3000–4000ms if you want longer
  await sleep(1200);
  if (runId !== aiWriteRunId) return; // canceled by a newer run

  // start typing markdown progressively
  await typeMarkdownProgressive(typeTarget, mdText, runId);

  // remove the thinking line when finished (optional)
  if (thinking && thinking.parentNode) thinking.remove();
}

// progressively reveal Markdown: re-render the slice safely
async function typeMarkdownProgressive(container, mdText, runId) {
  // Guard: require marked + DOMPurify
  if (typeof marked === "undefined" || typeof DOMPurify === "undefined") {
    container.textContent = mdText; // fallback to plain text
    return;
  }

  let i = 0;
  let lastUpdate = 0;
  const n = mdText.length;

  while (i < n) {
    if (runId !== aiWriteRunId) return; // canceled

    const ch = mdText[i++];
    // pacing: pause more on punctuation to feel natural
    // const delay = /[.?!…]/.test(ch) ? 70 : 18;
    // await sleep(delay);

    // update HTML every ~40ms or at newline to reduce CPU
    const now = performance.now();
    if (now - lastUpdate > 40 || ch === "\n" || i === n) {
      const partial = mdText.slice(0, i);
      const html = DOMPurify.sanitize(marked.parse(partial, { breaks: true }));
      container.innerHTML = html;
      lastUpdate = now;
    }
  }
}


// progressively reveal Markdown: re-render the slice safely
async function typeMarkdownProgressive(container, mdText, runId) {
  // Guard: require marked + DOMPurify
  if (typeof marked === "undefined" || typeof DOMPurify === "undefined") {
    container.textContent = mdText; // fallback to plain text
    return;
  }

  let i = 0;
  let lastUpdate = 0;
  const n = mdText.length;

  while (i < n) {
    if (runId !== aiWriteRunId) return; // canceled

    const ch = mdText[i++];
    // pacing: pause more on punctuation to feel natural
    const delay = /[.?!…]/.test(ch) ? 70 : 18;
    await sleep(delay);

    // update HTML every ~40ms or at newline to reduce CPU
    const now = performance.now();
    if (now - lastUpdate > 40 || ch === "\n" || i === n) {
      const partial = mdText.slice(0, i);
      const html = DOMPurify.sanitize(marked.parse(partial, { breaks: true }));
      container.innerHTML = html;
      lastUpdate = now;
    }
  }
}


// // simple card grid
// function renderCards(items){
//   return `
//   <div class="row row-cols-1 row-cols-sm-2 row-cols-md-3 row-cols-lg-4 g-3">
//     ${items.map(it => `
//       <div class="col">
//         <div class="card h-100 shadow-sm">
//           ${it.images && it.images.length ? `
//             <img src="${it.images[0]}" class="card-img-top" alt="${it.title}" loading="lazy" style="object-fit:cover;max-height:200px">
//           ` : ``}
//           <div class="card-body d-flex flex-column">
//             <h6 class="card-title"><a href="${it.url}" target="_blank" rel="noopener">${it.title || "Objekt"}</a></h6>
//             <div class="small text-muted mb-2">
//               ${it.currency ? `${it.currency}` : ""} ${it.current_bid ?? ""} ${it.location ? `· ${it.location}` : ""}
//             </div>
//             ${it.info_text ? `<p class="small text-muted">${it.info_text}</p>` : ``}
//             <div class="mt-auto small text-muted">ID: ${it.id}</div>
//           </div>
//         </div>
//       </div>
//     `).join("")}
//   </div>`;
// }
