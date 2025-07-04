"""
채널과 채팅 테이블 마이그레이션 스크립트
기존 데이터베이스에 새로운 테이블들을 추가합니다.
"""

from sqlalchemy import create_engine, text
from database import DATABASE_URL
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_channel_chat_tables():
    """채널과 채팅 관련 테이블들을 생성합니다."""
    
    engine = create_engine(DATABASE_URL)
    
    # 마이그레이션 SQL 문들
    migrations = [
        # 채널 테이블 생성
        """
        CREATE TABLE IF NOT EXISTS channels (
            id SERIAL PRIMARY KEY,
            project_id VARCHAR(6) NOT NULL,
            channel_id VARCHAR(100) NOT NULL,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            is_public BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL,
            UNIQUE(channel_id)
        );
        """,
        
        # 채널 멤버 관계 테이블 생성
        """
        CREATE TABLE IF NOT EXISTS channel_members (
            channel_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            role VARCHAR(50) DEFAULT 'member',
            PRIMARY KEY (channel_id, user_id),
            FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """,
        
        # 채팅 테이블 생성
        """
        CREATE TABLE IF NOT EXISTS chat (
            id SERIAL PRIMARY KEY,
            project_id VARCHAR(6) NOT NULL,
            channel_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """,
        
        # 인덱스 생성
        """
        CREATE INDEX IF NOT EXISTS idx_channels_project_id ON channels(project_id);
        CREATE INDEX IF NOT EXISTS idx_channels_channel_id ON channels(channel_id);
        CREATE INDEX IF NOT EXISTS idx_channel_members_channel_id ON channel_members(channel_id);
        CREATE INDEX IF NOT EXISTS idx_channel_members_user_id ON channel_members(user_id);
        CREATE INDEX IF NOT EXISTS idx_chat_channel_id ON chat(channel_id);
        CREATE INDEX IF NOT EXISTS idx_chat_user_id ON chat(user_id);
        CREATE INDEX IF NOT EXISTS idx_chat_timestamp ON chat(timestamp);
        CREATE INDEX IF NOT EXISTS idx_chat_project_id ON chat(project_id);
        """
    ]
    
    try:
        with engine.connect() as conn:
            for i, migration in enumerate(migrations, 1):
                logger.info(f"실행 중인 마이그레이션 {i}/{len(migrations)}")
                conn.execute(text(migration))
                conn.commit()
                logger.info(f"마이그레이션 {i} 완료")
        
        logger.info("모든 마이그레이션이 성공적으로 완료되었습니다!")
        
    except Exception as e:
        logger.error(f"마이그레이션 중 오류 발생: {e}")
        raise

def create_sample_data():
    """샘플 채널과 채팅 데이터를 생성합니다."""
    
    engine = create_engine(DATABASE_URL)
    
    sample_data = [
        # 샘플 채널 생성
        """
        INSERT INTO channels (project_id, channel_id, name, description, is_public, created_by)
        VALUES 
        ('PROJ01', 'general', '일반', '프로젝트 전체 공지사항', TRUE, 1),
        ('PROJ01', 'dev-team', '개발팀', '개발 관련 논의', FALSE, 1),
        ('PROJ01', 'design-team', '디자인팀', '디자인 관련 논의', FALSE, 1)
        ON CONFLICT (channel_id) DO NOTHING;
        """,
        
        # 샘플 채널 멤버 추가
        """
        INSERT INTO channel_members (channel_id, user_id, role)
        SELECT c.id, u.id, 'member'
        FROM channels c, users u
        WHERE c.channel_id = 'general' AND u.id IN (1, 2, 3)
        ON CONFLICT (channel_id, user_id) DO NOTHING;
        """,
        
        # 샘플 채팅 메시지 추가
        """
        INSERT INTO chat (project_id, channel_id, user_id, message)
        SELECT 
            'PROJ01',
            c.id,
            u.id,
            '안녕하세요! 프로젝트를 시작합니다.'
        FROM channels c, users u
        WHERE c.channel_id = 'general' AND u.id = 1
        ON CONFLICT DO NOTHING;
        """
    ]
    
    try:
        with engine.connect() as conn:
            for i, data in enumerate(sample_data, 1):
                logger.info(f"샘플 데이터 생성 중 {i}/{len(sample_data)}")
                conn.execute(text(data))
                conn.commit()
                logger.info(f"샘플 데이터 {i} 생성 완료")
        
        logger.info("샘플 데이터 생성이 완료되었습니다!")
        
    except Exception as e:
        logger.error(f"샘플 데이터 생성 중 오류 발생: {e}")
        raise

if __name__ == "__main__":
    print("채널과 채팅 테이블 마이그레이션을 시작합니다...")
    
    # 테이블 생성
    migrate_channel_chat_tables()
    
    # 샘플 데이터 생성 (선택사항)
    create_sample = input("샘플 데이터를 생성하시겠습니까? (y/n): ").lower().strip()
    if create_sample == 'y':
        create_sample_data()
    
    print("마이그레이션이 완료되었습니다!") 