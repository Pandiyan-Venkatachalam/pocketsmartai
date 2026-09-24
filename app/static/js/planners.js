/**
 * PocketSmart AI - Planners and Recommendation Handlers
 */

function showLoading(msg = "Gemini is analyzing your budget and finding optimal products...") {
    let overlay = document.getElementById("loading-overlay");
    if (!overlay) {
        overlay = document.createElement("div");
        overlay.id = "loading-overlay";
        overlay.className = "loading-overlay";
        overlay.innerHTML = `
            <div class="spinner"></div>
            <p id="loading-msg" style="color: #fff; font-weight: 600; font-size: 1.1rem; text-align: center; max-width: 400px;"></p>
            <p style="color: #9ca3af; font-size: 0.85rem;">Checking verified catalog from Amazon, IKEA, Flipkart & more...</p>
        `;
        document.body.appendChild(overlay);
    }
    const msgEl = document.getElementById("loading-msg");
    if (msgEl) msgEl.innerText = msg;
    overlay.classList.add("active");
}

function hideLoading() {
    const overlay = document.getElementById("loading-overlay");
    if (overlay) overlay.classList.remove("active");
}

document.addEventListener("DOMContentLoaded", () => {
    // =========================================================================
    // 1. Home Interior Planner
    // =========================================================================
    const homeForm = document.getElementById("home-planner-form");
    if (homeForm) {
        homeForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const budget = parseFloat(document.getElementById("total_budget").value);
            const roomType = document.getElementById("room_type").value;
            const style = document.getElementById("style").value;
            const additional = document.getElementById("additional_preferences").value;

            // Collect selected items
            const requiredItems = [];
            const quantities = {};
            const checkboxes = document.querySelectorAll(".home-item-checkbox:checked");
            checkboxes.forEach(cb => {
                const item = cb.value;
                requiredItems.push(item);
                const qtyInput = document.getElementById(`qty_${item.toLowerCase().replace(/\s+/g, '_')}`);
                quantities[item] = qtyInput ? parseInt(qtyInput.value) || 1 : 1;
            });

            if (requiredItems.length === 0) {
                // If none checked, add defaults
                requiredItems.push("Sofa", "Lights");
            }

            showLoading("Gemini is designing your interior layout and balancing product prices...");

            try {
                const res = await fetch("/api/planners/home", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        total_budget: budget,
                        room_type: roomType,
                        style: style,
                        required_items: requiredItems,
                        quantities: quantities,
                        additional_preferences: additional
                    })
                });

                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || "Unable to generate home recommendation.");
                }

                window.location.href = `/recommendations/${data.recommendation_id}`;
            } catch (err) {
                hideLoading();
                alert(err.message);
            }
        });
    }

    // =========================================================================
    // 2. Party Budget Planner
    // =========================================================================
    const partyForm = document.getElementById("party-planner-form");
    if (partyForm) {
        partyForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const budget = parseFloat(document.getElementById("budget").value);
            const guestCount = parseInt(document.getElementById("guest_count").value);
            const location = document.getElementById("location").value;
            const eventDate = document.getElementById("event_date").value;

            // Read typed custom wish if present, otherwise fall back to dropdown selection
            const customEventVal = document.getElementById("custom_event_type") ? document.getElementById("custom_event_type").value.trim() : "";
            const eventType = customEventVal || document.getElementById("event_type").value;

            const customFoodVal = document.getElementById("custom_food") ? document.getElementById("custom_food").value.trim() : "";
            let foodPref = customFoodVal || document.getElementById("food_preferences").value;

            const customDecorVal = document.getElementById("custom_decor") ? document.getElementById("custom_decor").value.trim() : "";
            const decorPref = customDecorVal || document.getElementById("decoration_preferences").value;

            const customEntVal = document.getElementById("custom_entertainment") ? document.getElementById("custom_entertainment").value.trim() : "";
            const entPref = customEntVal || document.getElementById("entertainment_preferences").value;

            const extraWishes = document.getElementById("additional_party_wishes") ? document.getElementById("additional_party_wishes").value.trim() : "";
            if (extraWishes) {
                foodPref += ` (Additional wishes: ${extraWishes})`;
            }

            showLoading(`Gemini is budgeting your custom "${eventType}" across Catering, Venue, Decor & Music...`);

            try {
                const res = await fetch("/api/planners/party", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        budget: budget,
                        event_type: eventType,
                        guest_count: guestCount,
                        location: location,
                        event_date: eventDate,
                        food_preferences: foodPref,
                        decoration_preferences: decorPref,
                        entertainment_preferences: entPref
                    })
                });

                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || "Unable to generate party recommendation.");
                }

                window.location.href = `/recommendations/${data.recommendation_id}`;
            } catch (err) {
                hideLoading();
                alert(err.message);
            }
        });
    }

    // =========================================================================
    // 2B. Universal Custom Budget Planner
    // =========================================================================
    const customForm = document.getElementById("custom-planner-form");
    if (customForm) {
        customForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const planTitle = document.getElementById("plan_title").value.trim();
            const budget = parseFloat(document.getElementById("budget").value);
            const categorySelect = document.getElementById("category_select").value;
            const customCategory = document.getElementById("custom_category_input") ? document.getElementById("custom_category_input").value.trim() : "";
            const targetItemsRaw = document.getElementById("target_items") ? document.getElementById("target_items").value.trim() : "";
            const targetItems = targetItemsRaw ? targetItemsRaw.split(",").map(i => i.trim()).filter(i => i) : [];
            const preferences = document.getElementById("preferences") ? document.getElementById("preferences").value.trim() : "";

            showLoading(`Gemini is curating budget-aware options for "${planTitle}"...`);

            try {
                const res = await fetch("/api/planners/custom", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        plan_title: planTitle,
                        budget: budget,
                        category: categorySelect,
                        custom_category: customCategory,
                        target_items: targetItems,
                        preferences: preferences
                    })
                });

                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || "Unable to generate custom recommendation.");
                }

                window.location.href = `/recommendations/${data.recommendation_id}`;
            } catch (err) {
                hideLoading();
                alert(err.message);
            }
        });
    }

    // =========================================================================
    // 3. Jewelry Budget Planner (with Multimodal Image Upload)
    // =========================================================================
    const jewelryForm = document.getElementById("jewelry-planner-form");
    if (jewelryForm) {
        const fileInput = document.getElementById("outfit_image");
        const dropzone = document.getElementById("image-dropzone");
        const previewContainer = document.getElementById("image-preview-box");
        const previewImg = document.getElementById("preview-img");
        const removeImgBtn = document.getElementById("remove-img-btn");

        if (dropzone && fileInput) {
            dropzone.addEventListener("click", () => fileInput.click());
            dropzone.addEventListener("dragover", (e) => {
                e.preventDefault();
                dropzone.classList.add("dragover");
            });
            dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
            dropzone.addEventListener("drop", (e) => {
                e.preventDefault();
                dropzone.classList.remove("dragover");
                if (e.dataTransfer.files.length > 0) {
                    fileInput.files = e.dataTransfer.files;
                    handleImagePreview(fileInput.files[0]);
                }
            });

            fileInput.addEventListener("change", () => {
                if (fileInput.files.length > 0) {
                    handleImagePreview(fileInput.files[0]);
                }
            });
        }

        function handleImagePreview(file) {
            if (!file.type.startsWith("image/")) {
                alert("Please select a valid image file (JPEG, PNG, WEBP).");
                return;
            }
            const reader = new FileReader();
            reader.onload = (e) => {
                if (previewImg) previewImg.src = e.target.result;
                if (previewContainer) previewContainer.style.display = "inline-block";
                if (dropzone) dropzone.style.display = "none";
            };
            reader.readAsDataURL(file);
        }

        if (removeImgBtn) {
            removeImgBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                if (fileInput) fileInput.value = "";
                if (previewContainer) previewContainer.style.display = "none";
                if (dropzone) dropzone.style.display = "block";
            });
        }

        jewelryForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const budget = document.getElementById("budget").value;
            const occasion = document.getElementById("occasion").value;
            const preferredStyle = document.getElementById("preferred_style").value;
            const colorPreference = document.getElementById("color_preference").value;

            // Jewelry types
            const types = [];
            document.querySelectorAll(".jewelry-type-checkbox:checked").forEach(cb => {
                types.push(cb.value);
            });

            const formData = new FormData();
            formData.append("budget", budget);
            formData.append("occasion", occasion);
            formData.append("preferred_style", preferredStyle);
            formData.append("jewelry_types", types.join(","));
            formData.append("color_preference", colorPreference);

            if (fileInput && fileInput.files.length > 0) {
                formData.append("outfit_image", fileInput.files[0]);
                showLoading("Gemini Multimodal Vision is analyzing your outfit's neckline, colors & aesthetic...");
            } else {
                showLoading("Gemini is selecting occasion-tailored jewelry options...");
            }

            try {
                const res = await fetch("/api/planners/jewelry", {
                    method: "POST",
                    body: formData
                });

                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || "Unable to generate jewelry recommendation.");
                }

                window.location.href = `/recommendations/${data.recommendation_id}`;
            } catch (err) {
                hideLoading();
                alert(err.message);
            }
        });
    }

    // =========================================================================
    // 4. History Actions (Delete)
    // =========================================================================
    document.querySelectorAll(".delete-history-btn").forEach(btn => {
        btn.addEventListener("click", async (e) => {
            const id = btn.getAttribute("data-id");
            if (!confirm(`Are you sure you want to delete recommendation #${id}?`)) return;

            try {
                const res = await fetch(`/api/history/${id}`, { method: "DELETE" });
                if (res.ok) {
                    const row = document.getElementById(`history-row-${id}`);
                    if (row) row.remove();
                    showToast("Plan deleted from history.", "success");
                } else {
                    alert("Failed to delete recommendation.");
                }
            } catch (err) {
                console.error(err);
                alert("Network error.");
            }
        });
    });
});
