#include "nxc_i18n.hpp"
#include <switch.h>
#include <map>

namespace nxc {

static bool g_es = false;

static const std::map<std::string, std::pair<std::string, std::string>> kStrings = {
    // key                      English                                  Spanish
    {"app/title",              {"NX Control",                           "NX Control"}},
    {"tab/today",              {"Today",                                "Hoy"}},
    {"tab/profiles",           {"Profiles",                             "Perfiles"}},
    {"tab/settings",           {"Settings",                             "Ajustes"}},
    {"today/no_service",       {"The NX Control service is not running. Restart the console.",
                                "El servicio de NX Control no está en marcha. Reinicia la consola."}},
    {"today/no_profiles",      {"No profiles yet. Set one up in Profiles.",
                                "Aún no hay perfiles. Configura uno en Perfiles."}},
    {"today/played",           {"Played today",                         "Jugado hoy"}},
    {"today/remaining",        {"Time remaining",                       "Tiempo restante"}},
    {"today/status",           {"Status",                               "Estado"}},
    {"today/now",              {"Right now",                            "Ahora mismo"}},
    {"today/no_game",          {"No game running",                      "Ningún juego abierto"}},
    {"today/playing",          {"Playing",                              "Jugando"}},
    {"unlimited",              {"Unlimited",                            "Sin límite"}},
    {"state/idle",             {"Idle",                                 "Inactivo"}},
    {"state/playing",          {"Playing",                              "Jugando"}},
    {"state/warning",          {"Almost out of time",                   "Queda poco tiempo"}},
    {"state/grace",            {"Grace period",                         "Tiempo de gracia"}},
    {"state/exhausted",        {"Time is up",                           "Tiempo agotado"}},
    {"state/outside_window",   {"Outside allowed hours",                "Fuera de horario"}},
    {"state/blocked",          {"Blocked",                              "Bloqueado"}},
    {"profiles/header",        {"Console users",                        "Usuarios de la consola"}},
    {"profiles/sub",           {"Choose a user to set up their rules",  "Elige un usuario para configurar sus reglas"}},
    {"mode/title",             {"Mode",                                 "Modo"}},
    {"mode/none",              {"Not managed",                          "Sin gestionar"}},
    {"mode/supervised",        {"Supervised",                           "Supervisado"}},
    {"mode/self",              {"Self-managed",                         "Autogestionado"}},
    {"mode/analytics",         {"Analytics only",                       "Solo analítica"}},
    {"daily/header",           {"Daily play time",                      "Tiempo de juego diario"}},
    {"daily/apply_all",        {"Apply Monday's time to every day",     "Aplicar el tiempo del lunes a todos los días"}},
    {"day/0",                  {"Monday",                               "Lunes"}},
    {"day/1",                  {"Tuesday",                              "Martes"}},
    {"day/2",                  {"Wednesday",                            "Miércoles"}},
    {"day/3",                  {"Thursday",                             "Jueves"}},
    {"day/4",                  {"Friday",                               "Viernes"}},
    {"day/5",                  {"Saturday",                             "Sábado"}},
    {"day/6",                  {"Sunday",                               "Domingo"}},
    {"min/none",               {"No play",                              "Sin juego"}},
    {"hours/header",           {"Allowed hours",                        "Horario permitido"}},
    {"hours/enabled",          {"Limit play to certain hours",          "Limitar el juego a un horario"}},
    {"hours/wd_from",          {"Weekdays from",                        "Entre semana desde"}},
    {"hours/wd_to",            {"Weekdays until",                       "Entre semana hasta"}},
    {"hours/we_from",          {"Weekends from",                        "Fin de semana desde"}},
    {"hours/we_to",            {"Weekends until",                       "Fin de semana hasta"}},
    {"end/header",             {"When time is up",                      "Al acabarse el tiempo"}},
    {"end/grace",              {"Grace period",                         "Tiempo de gracia"}},
    {"end/close",              {"Close the game after",                 "Cerrar el juego tras"}},
    {"end/never",              {"Never (keep it suspended)",            "Nunca (dejarlo suspendido)"}},
    {"end/note",               {"The game is sent to HOME and paused, never closed unless you choose so.",
                                "El juego se manda al HOME y queda en pausa; solo se cierra si así lo eliges."}},
    {"saved",                  {"Saved",                                "Guardado"}},
    {"save_error",             {"Could not save the settings to the SD card",
                                "No se han podido guardar los ajustes en la SD"}},
    {"pin/header",             {"Security",                             "Seguridad"}},
    {"pin/change",             {"Change PIN",                           "Cambiar PIN"}},
    {"pin/create",             {"Create PIN",                           "Crear PIN"}},
    {"pin/enter",              {"Enter your NX Control PIN",            "Introduce el PIN de NX Control"}},
    {"pin/new",                {"Choose a PIN (4 to 8 digits)",         "Elige un PIN (de 4 a 8 cifras)"}},
    {"pin/repeat",             {"Repeat the PIN",                       "Repite el PIN"}},
    {"pin/mismatch",           {"The PINs do not match",                "Los PIN no coinciden"}},
    {"pin/invalid",            {"The PIN must have 4 to 8 digits",      "El PIN debe tener de 4 a 8 cifras"}},
    {"pin/wrong",              {"Wrong PIN",                            "PIN incorrecto"}},
    {"pin/set",                {"PIN saved",                            "PIN guardado"}},
    {"pin/unlock",             {"Unlock with PIN",                      "Desbloquear con PIN"}},
    {"pin/locked",             {"Settings are protected with a PIN.",   "Los ajustes están protegidos con PIN."}},
    {"pin/unlocked",           {"Unlocked",                             "Desbloqueado"}},
    {"welcome/text",           {"Welcome to NX Control!\n\nFirst, create a PIN. It protects the settings so only you can change the rules.",
                                "¡Bienvenido a NX Control!\n\nPrimero, crea un PIN. Protege los ajustes para que solo tú puedas cambiar las reglas."}},
    {"welcome/later",          {"Later",                                "Más tarde"}},
    {"ok",                     {"OK",                                   "Aceptar"}},
    {"net/header",             {"Network and Home Assistant",           "Red y Home Assistant"}},
    {"net/enabled",            {"Local network access",                 "Acceso desde la red local"}},
    {"net/note",               {"Needed for the web panel and Home Assistant.",
                                "Necesario para el panel web y Home Assistant."}},
    {"about/header",           {"About",                                "Acerca de"}},
    {"about/version",          {"Version",                              "Versión"}},
};

void initLanguage() {
    u64 code = 0;
    SetLanguage lang = SetLanguage_ENUS;
    if (R_SUCCEEDED(setInitialize())) {
        if (R_SUCCEEDED(setGetSystemLanguage(&code))) setMakeLanguage(code, &lang);
        setExit();
    }
    g_es = (lang == SetLanguage_ES || lang == SetLanguage_ES419);
}

bool isSpanish() { return g_es; }

const std::string& tr(const char* key) {
    static const std::string missing = "?";
    auto it = kStrings.find(key);
    if (it == kStrings.end()) return missing;
    return g_es ? it->second.second : it->second.first;
}

} // namespace nxc
