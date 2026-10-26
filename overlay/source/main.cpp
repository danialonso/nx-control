// NX Control - quick panel (Tesla overlay)
#define TESLA_INIT_IMPL
#include <tesla.hpp>
#include <nlohmann/json.hpp>
#include <cstdio>
#include <cstdlib>
#include <string>

using nlohmann::json;

namespace {

constexpr const char *kStatePath = "sdmc:/config/nxcontrol/state.json";

// ------------------------------------------------------------------ texts
// One column per language: English, Spanish, French, German, Italian, Portuguese.
struct Text { const char *key; const char *t[6]; };
const Text kTexts[] = {
    {"unlimited",  {"Unlimited", "Sin límite", "Illimité", "Unbegrenzt", "Illimitato", "Sem limite"}},
    {"today",      {"Today", "Hoy", "Aujourd'hui", "Heute", "Oggi", "Hoje"}},
    {"profile",    {"Profile", "Perfil", "Profil", "Profil", "Profilo", "Perfil"}},
    {"remaining",  {"Time remaining", "Tiempo restante", "Temps restant", "Verbleibende Zeit", "Tempo rimanente", "Tempo restante"}},
    {"played",     {"Played today", "Jugado hoy", "Joué aujourd'hui", "Heute gespielt", "Giocato oggi", "Jogado hoje"}},
    {"status",     {"Status", "Estado", "État", "Status", "Stato", "Estado"}},
    {"more_time",  {"Need more time?", "¿Necesitas más tiempo?", "Besoin de plus de temps ?", "Mehr Zeit nötig?",
                    "Ti serve più tempo?", "Precisa de mais tempo?"}},
    {"request",    {"Request", "Solicitud", "Demande", "Anfrage", "Richiesta", "Pedido"}},
    {"ask",        {"Ask for %d more minutes", "Pedir %d minutos más", "Demander %d minutes de plus", "Um %d Minuten mehr bitten",
                    "Chiedi %d minuti in più", "Pedir mais %d minutos"}},
    {"no_game",    {"No game running", "Ningún juego abierto", "Aucun jeu ouvert", "Kein Spiel geöffnet", "Nessun gioco aperto",
                    "Nenhum jogo aberto"}},
    {"sent",       {"Sent, waiting...", "Enviada, esperando...", "Envoyée, en attente...", "Gesendet, warte...", "Inviata, in attesa...",
                    "Enviado, a aguardar..."}},
    {"not_sent",   {"Could not send", "No se pudo enviar", "Envoi impossible", "Senden fehlgeschlagen", "Impossibile inviare",
                    "Não foi possível enviar"}},
    {"no_service", {"Service not running", "El servicio no está en marcha", "Le service ne fonctionne pas", "Dienst läuft nicht",
                    "Servizio non in esecuzione", "O serviço não está em execução"}},
    {"waiting",    {"Waiting", "Esperando", "En attente", "Wartet", "In attesa", "A aguardar"}},
    {"approved",   {"Approved", "Aprobada", "Acceptée", "Genehmigt", "Approvata", "Aprovado"}},
    {"denied",     {"Denied", "Denegada", "Refusée", "Abgelehnt", "Rifiutata", "Recusado"}},
    {"not_config", {"Not configured", "Sin configurar", "Non configuré", "Nicht eingerichtet", "Non configurato", "Não configurado"}},
    {"st_idle",    {"Idle", "Inactivo", "Inactif", "Inaktiv", "Inattivo", "Inativo"}},
    {"st_playing", {"Playing", "Jugando", "En jeu", "Spielt", "In gioco", "A jogar"}},
    {"st_warning", {"Almost out of time", "Queda poco tiempo", "Bientôt plus de temps", "Zeit fast abgelaufen", "Tempo quasi finito",
                    "Resta pouco tempo"}},
    {"st_grace",   {"Grace period", "Tiempo de gracia", "Délai de grâce", "Nachfrist", "Periodo di tolleranza", "Tempo de tolerância"}},
    {"st_exhausted", {"Time is up", "Se acabó el tiempo", "Temps écoulé", "Zeit abgelaufen", "Tempo scaduto", "O tempo acabou"}},
    {"st_outside_window", {"Outside allowed hours", "Fuera del horario permitido", "En dehors des horaires autorisés",
                    "Außerhalb der erlaubten Zeiten", "Fuori dall'orario consentito", "Fora do horário permitido"}},
    {"st_blocked", {"Blocked", "Bloqueado", "Bloqué", "Gesperrt", "Bloccato", "Bloqueado"}},
};

int language() {
    static int lang = -1;
    if (lang < 0) {
        lang = 0;
        u64 code = 0;
        SetLanguage l = SetLanguage_ENUS;
        if (R_SUCCEEDED(setInitialize())) {
            if (R_SUCCEEDED(setGetSystemLanguage(&code)) && R_SUCCEEDED(setMakeLanguage(code, &l))) {
                switch (l) {
                    case SetLanguage_ES: case SetLanguage_ES419: lang = 1; break;
                    case SetLanguage_FR: case SetLanguage_FRCA:  lang = 2; break;
                    case SetLanguage_DE:                         lang = 3; break;
                    case SetLanguage_IT:                         lang = 4; break;
                    case SetLanguage_PT: case SetLanguage_PTBR:  lang = 5; break;
                    default: break;
                }
            }
            setExit();
        }
    }
    return lang;
}

std::string T(const std::string &key) {
    for (const auto &e : kTexts)
        if (key == e.key) return e.t[language()];
    return std::string();
}

std::string formatDuration(long long seconds) {
    if (seconds < 0) return T("unlimited");
    char buf[32];
    if (seconds >= 3600) std::snprintf(buf, sizeof(buf), "%lldh %02lldm", seconds / 3600, (seconds % 3600) / 60);
    else                 std::snprintf(buf, sizeof(buf), "%lldm %02llds", seconds / 60, seconds % 60);
    return buf;
}

json readState() {
    FILE *f = std::fopen(kStatePath, "rb");
    if (!f) return json();
    std::string text;
    char buf[1024]; size_t n;
    while ((n = std::fread(buf, 1, sizeof(buf), f)) > 0) text.append(buf, n);
    std::fclose(f);
    return json::parse(text, nullptr, false);
}

class MainGui : public tsl::Gui {
public:
    tsl::elm::Element *createUI() override {
        auto frame = new tsl::elm::OverlayFrame("NX Control", NXC_VERSION);
        auto list  = new tsl::elm::List();

        list->addItem(new tsl::elm::CategoryHeader(T("today")));
        profile_   = new tsl::elm::ListItem(T("profile"), "-");
        remaining_ = new tsl::elm::ListItem(T("remaining"), "-");
        used_      = new tsl::elm::ListItem(T("played"), "-");
        status_    = new tsl::elm::ListItem(T("status"), "-");
        list->addItem(profile_);
        list->addItem(remaining_);
        list->addItem(used_);
        list->addItem(status_);

        list->addItem(new tsl::elm::CategoryHeader(T("more_time")));
        request_ = new tsl::elm::ListItem(T("request"), "-");
        list->addItem(request_);
        for (int minutes : {15, 30, 60}) {
            char label[96];
            std::snprintf(label, sizeof(label), T("ask").c_str(), minutes);
            auto item = new tsl::elm::ListItem(label);
            item->setClickListener([this, minutes](u64 keys) {
                if (!(keys & HidNpadButton_A)) return false;
                sendRequest(minutes);
                return true;
            });
            list->addItem(item);
        }

        frame->setContent(list);
        refresh();
        return frame;
    }

    void update() override {
        if (++frames_ % 60 == 0) refresh();
    }

private:
    // The service picks up files from the inbox folder within a second.
    void sendRequest(int minutes) {
        if (profile_id_.empty()) {
            request_->setValue(T("no_game"));
            return;
        }
        json cmd = {{"type", "request"}, {"profile_id", profile_id_}, {"seconds", minutes * 60}};
        char base[96];
        std::snprintf(base, sizeof(base), "sdmc:/config/nxcontrol/inbox/ovl_%lu", armGetSystemTick());
        std::string tmp = std::string(base) + ".tmp", final_path = std::string(base) + ".json";
        if (FILE *f = std::fopen(tmp.c_str(), "wb")) {
            std::string out = cmd.dump();
            std::fwrite(out.data(), 1, out.size(), f);
            std::fclose(f);
            std::rename(tmp.c_str(), final_path.c_str());
            request_->setValue(T("sent"));
        } else {
            request_->setValue(T("not_sent"));
        }
    }

    void refresh() {
        json s = readState();
        if (s.is_discarded() || !s.is_object()) {
            status_->setValue(T("no_service"));
            return;
        }
        const json &session = s["session"];
        std::string pid = session.value("profile_id", std::string());
        profile_id_ = pid;
        std::string req = "-";
        if (s.contains("requests") && s["requests"].is_array())
            for (const auto &r : s["requests"])
                if (r.value("profile_id", std::string()) == pid) {
                    std::string st = r.value("status", std::string());
                    long long mins = r.value("seconds", 0LL) / 60;
                    if (st == "pending") req = T("waiting") + " (" + std::to_string(mins) + " min)";
                    else if (st == "approved") req = T("approved") + " (+" + std::to_string(mins) + " min)";
                    else if (st == "denied") req = T("denied");
                }
        request_->setValue(req);
        {
            std::string st = session.value("state", std::string("idle"));
            std::string text = T("st_" + st);
            status_->setValue(text.empty() ? st : text);
        }

        for (const auto &p : s["profiles"]) {
            if (p.value("id", std::string()) != pid) continue;
            profile_->setValue(p.value("name", std::string("-")));
            remaining_->setValue(formatDuration(p.value("remaining_today", -1LL)));
            used_->setValue(formatDuration(p.value("used_today", 0LL)));
            return;
        }
        profile_->setValue(pid.empty() ? T("no_game") : T("not_config"));
        remaining_->setValue("-");
        used_->setValue("-");
    }

    tsl::elm::ListItem *profile_ = nullptr, *remaining_ = nullptr, *used_ = nullptr, *status_ = nullptr;
    tsl::elm::ListItem *request_ = nullptr;
    std::string profile_id_;
    u32 frames_ = 0;
};

class NxControlOverlay : public tsl::Overlay {
public:
    void initServices() override { fsdevMountSdmc(); }
    void exitServices() override {}
    std::unique_ptr<tsl::Gui> loadInitialGui() override { return initially<MainGui>(); }
};

} // namespace

int main(int argc, char **argv) {
    return tsl::loop<NxControlOverlay>(argc, argv);
}
