 // reviews.js - peer review UI (student + leader dashboards). No custom colours: uses existing page classes.
(function () {
    const API = "http://127.0.0.1:8000";
    const userId = localStorage.getItem("userId");
    const isLeaderPage = !!document.querySelector(".dashboard-section");
    const cardClass = isLeaderPage ? "project-form" : "project";
    const btnClass = "login-btn";

    function el(tag, text, cls) {
        const e = document.createElement(tag);
        if (text !== undefined && text !== null) e.textContent = text;
        if (cls) e.className = cls;
        return e;
    }

    function fmt(d) {
        if (!d) return "";
        const x = new Date(d);
        return isNaN(x) ? String(d) : x.toLocaleDateString();
    }

    async function getJson(url, options) {
        const r = await fetch(url, options);
        const data = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(data.detail || data.message || ("Request failed (" + r.status + ")"));
        return data;
    }

    function firstArray(data) {
        if (Array.isArray(data)) return data;
        for (const k of ["teammates", "members", "team"]) if (Array.isArray(data[k])) return data[k];
        for (const k in data) if (Array.isArray(data[k])) return data[k];
        return [];
    }

    function buildTeammate(pid, t, msgBox, reload) {
        const id = t.User_ID ?? t.user_id ?? t.Reviewee_ID;
        const name = t.Name ?? t.name ?? ("User " + id);
        const role = t.Role_In_Project ?? t.Project_Role ?? t.Role ?? "";
        const hasReview = t.Rating !== null && t.Rating !== undefined;
        const canEdit = hasReview ? !!t.Can_Edit : true;

        const box = el("div", null, cardClass);
        box.style.paddingRight = "20px";
        box.appendChild(el("h4", role ? (name + " (" + role + ")") : name));

        const sel = document.createElement("select");
        for (let i = 5; i >= 1; i--) {
            const o = el("option", i + " / 5");
            o.value = String(i);
            sel.appendChild(o);
        }
        sel.value = hasReview ? String(t.Rating) : "5";

        const ta = document.createElement("textarea");
        ta.rows = 3;
        ta.maxLength = 2000;
        ta.placeholder = "Write your review for " + name;
        ta.value = hasReview ? (t.Comment || "") : "";
        ta.style.width = "100%";

        sel.disabled = !canEdit;
        ta.disabled = !canEdit;

        const btn = el("button", hasReview ? "Update Review" : "Save Review", btnClass);
        btn.type = "button";
        btn.disabled = !canEdit;
        btn.onclick = async function () {
            const comment = ta.value.trim();
            if (!comment) { msgBox.textContent = "Please write a comment."; return; }
            btn.disabled = true;
            try {
                await getJson(API + "/workflow/projects/" + pid + "/reviews", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        reviewer_id: Number(userId),
                        reviewee_id: Number(id),
                        rating: Number(sel.value),
                        comment: comment
                    })
                });
                msgBox.textContent = "Review saved.";
                reload();
            } catch (e) {
                msgBox.textContent = e.message;
                btn.disabled = false;
            }
        };

        box.appendChild(sel);
        box.appendChild(ta);
        box.appendChild(btn);

        if (hasReview) {
            let info = "Written on " + fmt(t.Created_At);
            if (t.Edited_At) info += " | Last edited on " + fmt(t.Edited_At);
            if (!canEdit) info += " | Edit window (7 days) is over";
            box.appendChild(el("p", info));
        }
        return box;
    }

    async function openForm(pid, holder) {
        holder.textContent = "Loading...";
        try {
            const data = await getJson(API + "/workflow/projects/" + pid + "/review-form?user_id=" + encodeURIComponent(userId));
            const list = firstArray(data);
            holder.textContent = "";
            const msgBox = el("p", "");
            holder.appendChild(msgBox);
            if (!list.length) { holder.appendChild(el("p", "No teammates to review.")); return; }
            list.forEach(t => holder.appendChild(buildTeammate(pid, t, msgBox, () => openForm(pid, holder))));
        } catch (e) {
            holder.textContent = e.message;
        }
    }

    async function loadReviews() {
        const area = document.getElementById("reviewsArea");
        if (!area || !userId) return;
        area.textContent = "";
        area.appendChild(el("h3", "Team Reviews"));
        try {
            const data = await getJson(API + "/workflow/users/" + encodeURIComponent(userId) + "/completed-projects");
            const projects = data.projects || [];
            if (!projects.length) {
                area.appendChild(el("p", "Reviews open after your mentor marks a project as completed."));
                return;
            }
            projects.forEach(p => {
                const card = el("div", null, cardClass);
                card.style.paddingRight = "20px";
                card.appendChild(el("h4", p.Project_Name));
                if (p.Completed_At) card.appendChild(el("p", "Completed on " + fmt(p.Completed_At)));
                const holder = el("div");
                const btn = el("button", "Write Reviews", btnClass);
                btn.type = "button";
                btn.onclick = () => openForm(p.Project_ID, holder);
                card.appendChild(btn);
                card.appendChild(holder);
                area.appendChild(card);
            });
        } catch (e) {
            area.appendChild(el("p", e.message));
        }
    }

    window.loadReviews = loadReviews;
    if (!isLeaderPage) loadReviews();
})();
