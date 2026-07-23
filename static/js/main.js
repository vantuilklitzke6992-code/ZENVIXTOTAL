document.addEventListener("DOMContentLoaded", function () {
    if (document.body.dataset.authenticated === "true") {
        const sendHeartbeat = () => fetch("/presenca/heartbeat", {
            method: "POST", credentials: "same-origin", keepalive: true
        }).catch(() => { });
        sendHeartbeat();
        window.setInterval(sendHeartbeat, 120000);

        // BEGIN CHANGE
        const socket = io();
        const chatWindow = document.querySelector(".chat-window");
        const chatForm = document.getElementById("chat-form");
        const chatInput = document.getElementById("chat-message-input");
        const notificationBanner = document.getElementById("chat-notification");

        const showChatNotification = (message) => {
            if (!notificationBanner) {
                return;
            }
            notificationBanner.textContent = message;
            notificationBanner.hidden = false;
            window.setTimeout(() => {
                notificationBanner.hidden = true;
            }, 5000);
        };

        if (chatWindow && chatForm && chatInput) {
            const serviceId = chatWindow.dataset.serviceId;
            if (serviceId) {
                socket.emit("join_service", { service_id: serviceId });
            }

            const renderMessage = (data) => {
                const messageElement = document.createElement("div");
                const isCurrentUser = Number(document.body.dataset.userId) === Number(data.remetente_id);
                messageElement.className = `chat-message ${isCurrentUser ? "chat-message-sent" : "chat-message-received"}`;
                messageElement.innerHTML = `
                    <div class="chat-meta">
                        <strong>${data.usuario}</strong>
                        <span>${data.criado_em || "Agora"}</span>
                    </div>
                    <p>${data.mensagem}</p>
                `;

                const emptyState = chatWindow.querySelector(".empty-state");
                if (emptyState) {
                    emptyState.remove();
                }

                chatWindow.appendChild(messageElement);
                chatWindow.scrollTop = chatWindow.scrollHeight;
            };

            socket.on("nova_mensagem", (data) => {
                if (serviceId && Number(data.service_id) === Number(serviceId)) {
                    renderMessage(data);
                }
            });

            chatForm.addEventListener("submit", async function (event) {
                event.preventDefault();
                const message = chatInput.value.trim();
                if (!message) {
                    return;
                }

                try {
                    const formData = new FormData(chatForm);
                    const response = await fetch(chatForm.action, {
                        method: "POST",
                        credentials: "same-origin",
                        headers: {
                            "X-Requested-With": "XMLHttpRequest"
                        },
                        body: formData
                    });

                    if (response.ok) {
                        const payload = await response.json();
                        renderMessage(payload.payload);
                        chatInput.value = "";
                    } else {
                        window.location.reload();
                    }
                } catch (error) {
                    console.warn("Envio de chat falhou:", error);
                    window.location.reload();
                }
            });
        }

        // END CHANGE
    }

    const cadastroForm = document.getElementById("cadastro-form");
    if (!cadastroForm) {
        return;
    }

    const accountTypeInput = document.getElementById("account-type-input");
    const accountTypeCards = document.querySelectorAll(".account-type-card");
    const stepCards = document.querySelectorAll(".step-card");
    const stepNumber = document.getElementById("step-number");
    const stepTotal = document.getElementById("step-total");
    const stepProgress = document.getElementById("step-progress");
    const companyFields = document.querySelectorAll(".company-only");
    const professionalFields = document.querySelectorAll(".professional-only");
    const clientFields = document.querySelectorAll(".client-only");
    const step1Next = document.getElementById("step1-next");
    const step2Prev = document.getElementById("step2-prev");
    const step2Next = document.getElementById("step2-next");
    const step3Prev = document.getElementById("step3-prev");
    const validationMessage = document.getElementById("form-validation-message");

    let currentStep = 1;
    const totalSteps = 3;
    const initialStep = parseInt(cadastroForm.dataset.currentStep, 10) || 1;
    const initialAccountType = cadastroForm.dataset.accountType || accountTypeInput.value || "cliente";

    function updateStepper() {
        stepNumber.textContent = currentStep;
        stepTotal.textContent = totalSteps;
        const percent = ((currentStep - 1) / (totalSteps - 1)) * 100;
        stepProgress.style.width = `${percent}%`;
    }

    function showStep(step) {
        stepCards.forEach((card) => {
            card.classList.toggle("step-card-active", card.dataset.step === String(step));
        });
        currentStep = step;
        updateStepper();
        validationMessage.classList.add("hidden");
    }

    function showValidation(message) {
        validationMessage.textContent = message;
        validationMessage.classList.remove("hidden");
    }

    function selectAccountType(type) {
        accountTypeCards.forEach((card) => {
            const selected = card.dataset.accountType === type;
            card.classList.toggle("active", selected);
        });
        accountTypeInput.value = type;
        renderTypeFields(type);
    }

    function renderTypeFields(type) {
        companyFields.forEach((el) => el.classList.toggle("hidden", type !== "empresa"));
        professionalFields.forEach((el) => el.classList.toggle("hidden", type !== "profissional"));
        clientFields.forEach((el) => el.classList.toggle("hidden", type !== "cliente"));
        const accountLabel = document.querySelector(".form-group label[for='nome']");
        if (type === "empresa") {
            accountLabel.textContent = "Nome do responsável";
        } else {
            accountLabel.textContent = "Nome";
        }
    }

    function validateStep(step) {
        const type = accountTypeInput.value;

        if (step === 1) {
            if (!type) {
                showValidation("Selecione um tipo de conta para continuar.");
                return false;
            }
            return true;
        }

        if (step === 2) {
            const nome = document.getElementById("nome").value.trim();
            const email = document.getElementById("email").value.trim();
            const senha = document.getElementById("senha").value;
            const confirmSenha = document.getElementById("confirm_senha").value;
            const empresaNome = document.getElementById("empresa_nome").value.trim();

            if (type === "empresa" && !empresaNome) {
                showValidation("Informe o nome da empresa para continuar.");
                return false;
            }

            if (!nome || !email || !senha || !confirmSenha) {
                showValidation("Preencha todos os campos obrigatórios desta etapa.");
                return false;
            }

            if (!email.includes("@") || !email.includes(".")) {
                showValidation("Informe um e-mail válido.");
                return false;
            }

            if (senha !== confirmSenha) {
                showValidation("As senhas não conferem.");
                return false;
            }

            return true;
        }

        if (step === 3) {
            const estado = document.getElementById("estado").value.trim();
            const cidade = document.getElementById("cidade").value.trim();
            const telefone = document.getElementById("telefone").value.trim();

            if (!estado || !cidade || !telefone) {
                showValidation("Preencha os campos obrigatórios desta etapa.");
                return false;
            }

            if (type === "cliente") {
                return true;
            }

            if (type === "profissional") {
                const especialidade = document.getElementById("especialidade").value.trim();
                const bio = document.getElementById("bio").value.trim();
                const cpf = document.getElementById("cpf").value.trim();

                if (!especialidade || !bio || !cpf) {
                    showValidation("Preencha todos os dados profissionais obrigatórios para continuar.");
                    return false;
                }
                return true;
            }

            if (type === "empresa") {
                const cnpj = document.getElementById("cnpj").value.trim();

                if (!cnpj) {
                    showValidation("Preencha os dados da empresa para continuar.");
                    return false;
                }
                return true;
            }

            return true;
        }

        return true;
    }

    accountTypeCards.forEach((card) => {
        card.addEventListener("click", function () {
            selectAccountType(this.dataset.accountType);
        });
    });

    step1Next.addEventListener("click", function () {
        if (!validateStep(1)) {
            return;
        }
        showStep(2);
    });

    step2Prev.addEventListener("click", function () {
        showStep(1);
    });

    step2Next.addEventListener("click", function () {
        if (!validateStep(2)) {
            return;
        }
        showStep(3);
    });

    step3Prev.addEventListener("click", function () {
        showStep(2);
    });

    cadastroForm.addEventListener("submit", function (event) {
        if (!validateStep(3)) {
            event.preventDefault();
        }
    });

    accountTypeInput.value = initialAccountType;
    selectAccountType(initialAccountType);
    showStep(initialStep);
});
