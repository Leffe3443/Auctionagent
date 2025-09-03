
// CSRF (Django standard)
function getCookie(name){
  const v = `; ${document.cookie}`;
  const p = v.split(`; ${name}=`);
  if (p.length === 2) return p.pop().split(';').shift();
}

const form = document.getElementById("aiSearchForm");
const btn  = document.getElementById("aiRunBtn");
const out  = document.getElementById("aiResults");
const aithinkauctionsearch = document.getElementById("ai-thinkingauctionsearch");

form.addEventListener("submit", async (e) => {
  e.preventDefault(); // stop full reload

  const itemId = document.getElementById("itemidaisearch").value.trim();
  

  if (!itemId) {
    out.innerHTML = `<div class="alert alert-warning">Ange ett item-id.</div>`;
    return;
  }

  btn.disabled = true;
  const old = btn.textContent;
  btn.textContent = "Söker…";

  aithinkauctionsearch.style.visibility = "visible";

    const url = `api/auction-agent/ai/?itemid=${encodeURIComponent(itemId)}`;

  try {    

    const res = await fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
        "Content-Type": "application/json"
      },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();



    const md = data.response_ai_content || ""; // <-- resp.output_text from backend
    // console.log(md)
    const html = DOMPurify.sanitize(marked.parse(md, { breaks: true })); // convert + sanitize


    out.innerHTML = '';

    // Time.sleep(3-4 sekunder)
    // Animation that runs here "**Formulerar för läsbarheten**"

    out.innerHTML = `
    <div class="card mb-3">
        <div class="card-body">
        ${html}
        </div>
    </div>
    `;
  } catch (err) {
    out.innerHTML = `<div class="alert alert-danger">Fel: ${err.message || err}</div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = old;
    aithinkauctionsearch.style.visibility = 'hidden';

  }

});




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
//               ${it.currency ? `${it.currency}` : ""}  ${it.current_bid ?? ""} ${it.location ? `· ${it.location}` : ""}
//             </div>
//             ${it.info_text ? `<p class="small text-muted">${it.info_text}</p>` : ``}
//             <div class="mt-auto small text-muted">ID: ${it.id}</div>
//           </div>
//         </div>
//       </div>
//     `).join("")}
//   </div>`;
// }
