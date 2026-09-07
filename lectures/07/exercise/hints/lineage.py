# https://github.com/datahub-project/datahub/blob/master/metadata-ingestion/examples/library/lineage_emitter_rest.py
import datahub.emitter.mce_builder as builder
from datahub.emitter.rest_emitter import DatahubRestEmitter
import logging

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

HOST: str = "http://localhost:8080"

if __name__ == "__main__":
    log.info("Create Metadata Change Event for linage.")
    # Construct a lineage object.
    lineage_mce = builder.make_lineage_mce(
        upstream_urns=[
            builder.make_dataset_urn(
                platform="mysql", name="datahub.experiment", env="PROD"
            ),  # Upstream
            builder.make_dataset_urn(
                platform="mysql", name="datahub.results", env="PROD"
            ),  # Upstream
        ],
        downstream_urn=builder.make_dataset_urn(
            platform="mysql", name="datahub.analysis", env="PROD"
        ),  # Downstream
    )

    # Create an emitter to the GMS REST API.
    log.info("Create emitter for linage change.")
    emitter = DatahubRestEmitter(HOST)

    # Emit metadata!
    log.info("Emit change event.")
    emitter.emit_mce(lineage_mce)
