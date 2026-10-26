from test_multi_evidence import EvidenceSearcher

s = EvidenceSearcher("dataset")
# Check case_08
print("Case 08 search:", s.search_for_user("2026-09-15T09:00:00Z", "user_08", {"gabriel.costa@proton.me"}))
# Check case_09
print("Case 09 search:", s.search_for_user("2026-09-17T14:15:00Z", "user_61", {"k.appiah88@gmail.com"}))
# Check case_10
print("Case 10 search:", s.search_for_user("2026-09-18T10:00:00Z", "user_10", {"nadia.ionescu@yahoo.com", "nadia.petrescu@yahoo.com", "n.petrescu@yahoo.com"}))
