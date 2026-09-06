import os
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from src.msg import EmailClient, SMTPServer

if __name__ == "__main__":

    load_dotenv(Path(__file__).resolve().parent / ".env")

    attachment_path = Path(
        os.getenv("KUBECONFIGS_DIR", Path(__file__).resolve().parent.parent / "tmp")
    )
    attachment_files = list(attachment_path.glob("*-personal-sa-*.yaml"))

    ec = EmailClient(
        email=os.getenv("EMAIL", "<email>"),
        password=os.getenv("PASSWORD", "<password>"),
        smtp_server=SMTPServer.SDU,
    )

    current_year = datetime.now().strftime("%y")

    for attachment in attachment_files:

        user_name = attachment.name.split("-")[0]
        receiver_email: str = user_name + "@student.sdu.dk"

        msg = ec.create_msg(
            receiver_email=receiver_email,
            subject=f"[Kubeconfig] - Kubeconfig for exercises in Big Data and Data Science Technology, E{current_year}",
            body=f"Dear {user_name},\n\nHere is the kubeconfig file for the Kubernetes cluster which you will need for exercises in the Big Data and Data Science Technology course, E{current_year}.\n",
            attachment=attachment,
        )
        # ec.send_msg(receiver_email, msg)
