
import httpx


BASE_URL = "https://rxnav.nlm.nih.gov/REST"
SEARCH_TERM = "acetaminophen"
MAX_RESULTS = 5


def main() -> None:
    with httpx.Client(timeout=20) as client:
        response = client.get(
            f"{BASE_URL}/drugs.json",
            params={"name": SEARCH_TERM},
        )
        response.raise_for_status()

        payload = response.json()
        groups = payload.get("drugGroup", {}).get("conceptGroup") or []

        medicines = []

        for group in groups:
            if group.get("tty") != "SBD":
                continue

            for concept in group.get("conceptProperties") or []:
                if concept.get("suppress") != "N":
                    continue

                if concept.get("rxcui") and concept.get("name"):
                    medicines.append(concept)

                if len(medicines) >= MAX_RESULTS:
                    break

            if len(medicines) >= MAX_RESULTS:
                break

        if not medicines:
            print("No matching branded medicines found.")
            return

        for medicine in medicines:
            rxcui = medicine["rxcui"]

            response = client.get(
                f"{BASE_URL}/rxcui/{rxcui}/related.json",
                params={"tty": "IN"},
            )
            response.raise_for_status()

            related_groups = (
                response.json()
                .get("relatedGroup", {})
                .get("conceptGroup") or []
            )

            ingredients = []

            for group in related_groups:
                if group.get("tty") == "IN":
                    ingredients.extend(
                        group.get("conceptProperties") or []
                    )

            print(f"\nMedicine: {medicine['name']}")
            print(f"RxCUI: {rxcui}")
            print("Ingredients:")

            if not ingredients:
                print("  No ingredient concepts returned.")
                continue

            for ingredient in ingredients:
                print(
                    f"  - {ingredient['name']} "
                    f"(RxCUI: {ingredient['rxcui']})"
                )


if __name__ == "__main__":
    main()