import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "naisi-birthday" / "index.html"


class V31StaticChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = GAME.read_text(encoding="utf-8")

    def test_game_file_is_present_and_has_v31_marker(self):
        self.assertIn("V3.1", self.source)
        self.assertIn('id="world"', self.source)

    def test_public_build_does_not_reference_preview_audio_or_private_links(self):
        self.assertNotIn("mcp-preview", self.source)
        self.assertNotIn("private-family.html", self.source)
        self.assertNotIn("#k=", self.source)

    def test_audio_manifest_keeps_all_18_voice_keys_for_fallback(self):
        match = re.search(r"const CFG=(\{.*?\});\n", self.source)
        self.assertIsNotNone(match)
        cfg = json.loads(match.group(1))
        self.assertEqual(
            set(cfg["audio"]),
            {
                "intro", "start", "left", "right", "straight", "red", "green",
                "slow", "pedestrian", "roadwork", "breakdown", "fixed", "arrive",
                "reroute", "reward", "birthday", "turn", "dad",
            },
        )

    def test_local_birthday_audio_is_present_and_mapped_to_the_requested_scenes(self):
        arrival = ROOT / "naisi-birthday" / "audio" / "birthday-arrival.m4a"
        blessing = ROOT / "naisi-birthday" / "audio" / "dad-blessing.m4a"
        self.assertTrue(arrival.is_file())
        self.assertTrue(blessing.is_file())
        self.assertIn('"birthday":"audio/birthday-arrival.m4a"', self.source)
        self.assertIn('"dad":"audio/dad-blessing.m4a"', self.source)
        self.assertIn("function birthdayGift(){S.phase='gift';speak('reward'", self.source)
        self.assertIn("S.candles.size===6)speak('reward'", self.source)

    def test_navigation_fallback_prefers_natural_chinese_device_voice(self):
        self.assertIn("function naturalVoiceScore", self.source)
        self.assertIn("enhanced|premium|natural|neural|siri", self.source)
        self.assertIn("function pickVoice(){", self.source)
        self.assertIn("u.rate=.94;u.pitch=1.02", self.source)

    def test_cockpit_and_vehicle_specific_paths_exist(self):
        self.assertIn("world.traveling", self.source)
        self.assertIn("cab-view.cab-car", self.source)
        self.assertIn("S.vehicle==='car'", self.source)
        self.assertIn("S.vehicle==='train'", self.source)

    def test_deterministic_events_and_progress_recovery_exist(self):
        self.assertIn("function setSeed", self.source)
        self.assertIn("function persist", self.source)
        self.assertIn("function restore", self.source)
        self.assertIn("tripTotalSteps", self.source)
        self.assertIn("eventHistory", self.source)

    def test_six_station_specific_interactions_exist(self):
        for station in ("task-bus", "task-metro", "task-rail", "task-museum", "task-zoo", "task-airport"):
            self.assertIn(station, self.source)

    def test_metro_close_action_is_checked_before_generic_metro_actions(self):
        exact = self.source.index("if(a==='task-metro-close')")
        generic = self.source.index("if(a.startsWith('task-metro-'))")
        self.assertLess(exact, generic)

    def test_airport_actions_parse_the_final_action_index(self):
        self.assertIn("const index=Number(a.split('-').pop())", self.source)
        self.assertIn("task-airport-runway-", self.source)
        self.assertIn("试试左边跑道", self.source)

    def test_birthday_route_is_unlocked_after_one_station_and_has_express_path(self):
        self.assertIn("n.id==='birthday'?S.completed.size>=1", self.source)
        self.assertIn("id==='birthday'&&S.completed.size<1", self.source)
        self.assertIn("function expressBirthday", self.source)
        self.assertIn("birthday-express", self.source)
        self.assertIn("if(S.target==='birthday'||S.tripEvents>=2)return null", self.source)

    def test_uploaded_dad_video_is_found_and_played(self):
        self.assertIn("document.querySelector('#dadVideo video')", self.source)
        self.assertNotIn("$('dadVideo video')", self.source)

    def test_event_resolution_is_handled_by_the_capture_listener(self):
        self.assertIn("function handleStationAction(a){if(a==='resolve-event'){resolveEvent();return true}", self.source)

    def test_restored_event_history_stays_an_array_for_event_resolution(self):
        self.assertIn("['completed','taskDone','candles','visited'].includes(k)?new Set", self.source)
        self.assertIn("if(!Array.isArray(S.eventHistory))S.eventHistory=[...(S.eventHistory||[])]", self.source)
        self.assertIn("S.eventHistory.includes(kind)", self.source)
        self.assertIn("S.eventHistory.push(kind)", self.source)

    def test_destination_selection_skips_route_choice_and_prioritizes_birthday(self):
        self.assertIn("S.route=[...S.routes[0]]", self.source)
        self.assertIn("S.phase='cab'", self.source)
        self.assertIn("n.id==='birthday'||S.filter==='all'||n.kind===S.filter", self.source)
        self.assertIn("kid(`继续前往 ${get(next).name}`", self.source)
        self.assertIn("S.phase='travel';S.event=null;S.pendingNext=null;speak('roadwork','前方道路施工，已自动改走最快路线。')", self.source)
        self.assertIn("if(S.phase==='route'&&S.target&&nodes[S.target])", self.source)

    def test_local_child_photo_is_mapped_to_all_family_photo_slots(self):
        photo = ROOT / "naisi-birthday" / "assets" / "naisi.jpg"
        self.assertTrue(photo.is_file())
        self.assertIn("CFG.localPhotos={avatar:'assets/naisi.jpg',portrait:'assets/naisi.jpg',drawing:'assets/naisi.jpg'};", self.source)

    def test_hero_photo_shows_more_shoulders(self):
        self.assertIn(".hero-photo img{object-position:center 100%}", self.source)


if __name__ == "__main__":
    unittest.main()
