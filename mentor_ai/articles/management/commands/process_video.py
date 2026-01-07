from django.core.management.base import BaseCommand

from articles.models import VideoContent
import json

from articles.video_processing_service import VideoProcessingService


class Command(BaseCommand):
    help = 'Process a video: chunking + embeddings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--video-id',
            type=str,
            help='UUID of the VideoContent to process'
        )
        parser.add_argument(
            '--transcript-file',
            type=str,
            help='Path to a JSON file containing the transcript (optional - for manual usage)'
        )
        parser.add_argument(
            '--from-youtube',
            action='store_true',
            help='Fetch transcript automatically from YouTube (requires youtube-transcript-api)'
        )
        parser.add_argument(
            '--process-all-new',
            action='store_true',
            help='Process all videos with status=NEW'
        )

    def handle(self, *args, **options):
        service = VideoProcessingService()

        if options['video_id']:
            # Process a single video
            try:
                video = VideoContent.objects.get(id=options['video_id'])
                self.stdout.write(f"Processing video: {video.title}")

                # Determine transcript source
                if options['transcript_file']:
                    # Manual transcript from file
                    with open(options['transcript_file'], 'r', encoding='utf-8') as f:
                        transcript = json.load(f)
                    result = service.process_video_with_transcript(video, transcript)

                elif options['from_youtube']:
                    # Automatic transcript from YouTube
                    result = service.process_video_from_youtube(video)

                else:
                    self.stdout.write(self.style.ERROR(
                        'You must specify either --transcript-file or --from-youtube'
                    ))
                    return

                self.stdout.write(self.style.SUCCESS(
                    f"✓ Success! Created {result['chunks_created']} chunks"
                ))

            except VideoContent.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Video not found: {options['video_id']}")
                )
            except FileNotFoundError:
                self.stdout.write(
                    self.style.ERROR(f"File not found: {options['transcript_file']}")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error: {str(e)}")
                )

        elif options['process_all_new']:
            # Process all new videos – requires YouTube API
            if not options['from_youtube']:
                self.stdout.write(self.style.ERROR(
                    'Bulk processing requires --from-youtube'
                ))
                return

            videos = VideoContent.objects.filter(status=VideoContent.Status.NEW)
            total = videos.count()

            self.stdout.write(f"Found {total} videos to process")

            for i, video in enumerate(videos, 1):
                try:
                    self.stdout.write(f"[{i}/{total}] Processing: {video.title}")
                    result = service.process_video_from_youtube(video)
                    self.stdout.write(self.style.SUCCESS(
                        f"  ✓ {result['chunks_created']} chunks"
                    ))
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"  ✗ Error: {str(e)}")
                    )

        else:
            self.stdout.write(self.style.WARNING(
                'You must specify either --video-id or --process-all-new'
            ))

