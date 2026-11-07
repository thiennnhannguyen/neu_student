"""Bảng của M12. Không import model M11; đọc kết quả học tập qua hàm công khai của M11."""

from app.extensions import db
from app.models.base import MockMixin, fk, pk


class Career(MockMixin, db.Model):
    __tablename__ = "careers"
    id = pk()
    slug = db.Column(db.String(64), nullable=False, unique=True)
    name = db.Column(db.String(128), nullable=False)
    field = db.Column(db.String(64), nullable=False, server_default="")
    # Tên đã chuẩn hóa (D-194), để DB chặn trùng tên kể cả khi hai admin tạo cùng lúc.
    name_key = db.Column(db.String(128), nullable=False, server_default="")
    # Nội dung giới thiệu nằm ở dữ liệu để landing page sau này dùng lại (CR-03).
    name_en = db.Column(db.String(128))
    career_group = db.Column(db.String(64))
    objective = db.Column(db.Text)
    major_fit = db.Column(db.JSON)
    self_study = db.Column(db.JSON)
    self_study_note = db.Column(db.String(255))
    illustration_key = db.Column(db.String(32))
    tagline = db.Column(db.String(80))
    sort_order = db.Column(db.Integer)
    __table_args__ = (db.Index("uq_careers_name_key", "name_key", unique=True),)


class CareerVersion(MockMixin, db.Model):
    """Bản published không sửa được: có trigger trong migration, kèm kiểm tra ở service."""

    __tablename__ = "career_versions"
    id = pk()
    career_id = fk("careers.id")
    version = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(16), nullable=False, default="draft")
    published_at = db.Column(db.DateTime)
    __table_args__ = (
        db.UniqueConstraint("career_id", "version"),
        db.CheckConstraint("status IN ('draft', 'published')", name="status_valid"),
        db.CheckConstraint(
            "status <> 'published' OR published_at IS NOT NULL", name="published_has_time"
        ),
    )


class CareerNode(MockMixin, db.Model):
    __tablename__ = "career_nodes"
    id = pk()
    career_version_id = fk("career_versions.id")
    name = db.Column(db.String(128), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    short_desc = db.Column(db.String(120))
    deliverable = db.Column(db.Text)
    # Đích của khóa ngoại phức hợp từ career_requirements.
    __table_args__ = (db.UniqueConstraint("id", "career_version_id"),)


class Skill(MockMixin, db.Model):
    __tablename__ = "skills"
    id = pk()
    name = db.Column(db.String(128), nullable=False)
    kind = db.Column(db.String(16), nullable=False)
    name_key = db.Column(db.String(128), nullable=False, server_default="")
    short_desc = db.Column(db.String(120))
    level = db.Column(db.String(16))
    criteria = db.Column(db.Text)
    __table_args__ = (
        db.CheckConstraint("kind IN ('skill', 'project')", name="kind_valid"),
        db.Index("uq_skills_name_key", "name_key", unique=True),
    )


class CareerRequirement(MockMixin, db.Model):
    __tablename__ = "career_requirements"
    id = pk()
    career_version_id = fk("career_versions.id", index=True)
    career_node_id = db.Column(db.String(64), nullable=False)
    kind = db.Column(db.String(16), nullable=False)
    course_id = fk("courses.id", nullable=True)
    skill_id = fk("skills.id", nullable=True)
    weight = db.Column(db.Numeric(4, 2, asdecimal=True), nullable=False, default=1)
    source = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(16), nullable=False, default="draft")
    approved_by = fk("users.id", nullable=True)
    approved_at = db.Column(db.DateTime)
    # Rỗng là áp dụng cho mọi ngành. Có giá trị thì chỉ tính cho sinh viên của ngành đó (Q92).
    program_id = db.Column(db.String(64), db.ForeignKey("programs.id"))
    # Một dòng trong cẩm nang. Cùng khóa ở các ngành khác nhau là cùng một môn của nghề.
    subject_key = db.Column(db.String(64))
    subject_name = db.Column(db.String(128))
    # Khóa môn khác mà yêu cầu này đã bao gồm vì 2 dòng cẩm nang cùng 1 mã ở ngành này.
    also_covers = db.Column(db.JSON)
    priority = db.Column(db.String(16))
    purpose = db.Column(db.Text)
    __table_args__ = (
        db.ForeignKeyConstraint(
            ["career_node_id", "career_version_id"],
            ["career_nodes.id", "career_nodes.career_version_id"],
            name="fk_career_requirements_node_consistent",
            ondelete="RESTRICT",
        ),
        db.CheckConstraint("kind IN ('course', 'skill', 'project')", name="kind_valid"),
        db.CheckConstraint("weight > 0", name="weight_positive"),
        db.CheckConstraint("status IN ('draft', 'approved')", name="status_valid"),
        db.CheckConstraint(
            "status <> 'approved' OR approved_by IS NOT NULL", name="approved_has_approver"
        ),
        db.CheckConstraint(
            "(kind = 'course' AND course_id IS NOT NULL AND skill_id IS NULL) OR "
            "(kind <> 'course' AND skill_id IS NOT NULL AND course_id IS NULL)",
            name="target_matches_kind",
        ),
    )


class CourseSkillMapping(MockMixin, db.Model):
    """Chỉ để hiển thị và gợi ý, không bao giờ làm kỹ năng hoàn thành (R7)."""

    __tablename__ = "course_skill_mappings"
    id = pk()
    course_id = fk("courses.id", index=True)
    skill_id = fk("skills.id")
    purpose = db.Column(db.String(32), nullable=False)
    source = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(16), nullable=False, default="draft")
    approved_by = fk("users.id", nullable=True)
    approved_at = db.Column(db.DateTime)
    __table_args__ = (
        db.UniqueConstraint("course_id", "skill_id"),
        db.CheckConstraint("status IN ('draft', 'approved')", name="status_valid"),
        db.CheckConstraint(
            "status <> 'approved' OR approved_by IS NOT NULL", name="approved_has_approver"
        ),
    )


class StudentCareerGoal(MockMixin, db.Model):
    __tablename__ = "student_career_goals"
    id = pk()
    student_id = fk("students.id")
    career_id = fk("careers.id")
    is_primary = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())
    started_at = db.Column(db.DateTime, nullable=False)
    ended_at = db.Column(db.DateTime)
    __table_args__ = (
        db.Index(
            "uq_student_career_goals_one_primary",
            "student_id",
            unique=True,
            sqlite_where=db.text("is_primary = 1 AND ended_at IS NULL"),
        ),
    )


class SkillEvidence(MockMixin, db.Model):
    __tablename__ = "skill_evidences"
    id = pk()
    student_id = fk("students.id", index=True)
    skill_id = fk("skills.id")
    description = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(512))
    status = db.Column(db.String(16), nullable=False, default="pending")
    reviewed_by = fk("users.id", nullable=True)
    reviewed_at = db.Column(db.DateTime)
    review_note = db.Column(db.Text)
    __table_args__ = (
        db.CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="status_valid"),
    )


class LearningRoadmap(MockMixin, db.Model):
    __tablename__ = "learning_roadmaps"
    id = pk()
    student_id = fk("students.id", index=True)
    career_id = fk("careers.id")
    __table_args__ = (db.Index("uq_learning_roadmaps_student", "student_id", unique=True),)


class RoadmapVersion(MockMixin, db.Model):
    __tablename__ = "roadmap_versions"
    id = pk()
    roadmap_id = fk("learning_roadmaps.id")
    version = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(16), nullable=False)
    based_on_version_id = fk("roadmap_versions.id", nullable=True)
    created_by = fk("users.id", nullable=True)
    created_at = db.Column(db.DateTime, nullable=False)
    # Dấu dữ liệu lúc tạo bản này. Khác hiện tại nghĩa là bản đã cũ (R11).
    data_version = db.Column(db.Integer)
    career_version_id = db.Column(db.String(64), db.ForeignKey("career_versions.id"))
    rule_version = db.Column(db.String(32))
    infeasible = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    unplaced = db.Column(db.JSON)
    dismissed_stamp = db.Column(db.String(128))
    __table_args__ = (
        db.UniqueConstraint("roadmap_id", "version"),
        db.CheckConstraint("status IN ('active', 'proposal', 'archived')", name="status_valid"),
        db.Index(
            "uq_roadmap_versions_one_active",
            "roadmap_id",
            unique=True,
            sqlite_where=db.text("status = 'active'"),
        ),
    )


class RoadmapItem(MockMixin, db.Model):
    __tablename__ = "roadmap_items"
    id = pk()
    roadmap_version_id = fk("roadmap_versions.id", index=True)
    semester_id = fk("semesters.id", nullable=True)
    course_id = fk("courses.id", nullable=True)
    skill_id = fk("skills.id", nullable=True)
    confidence = db.Column(db.String(16), nullable=False)
    depends_on_pending_result = db.Column(
        db.Boolean, nullable=False, default=False, server_default=db.false()
    )
    outside_curriculum = db.Column(
        db.Boolean, nullable=False, default=False, server_default=db.false()
    )
    note = db.Column(db.Text)
    alignment = db.Column(db.String(16))
    alignment_offset = db.Column(db.Integer)
    planned_semester = db.Column(db.Integer)
    is_pinned = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    is_primary_career = db.Column(
        db.Boolean, nullable=False, default=False, server_default=db.false()
    )
    assumed_position = db.Column(
        db.Boolean, nullable=False, default=False, server_default=db.false()
    )
    __table_args__ = (
        db.CheckConstraint("confidence IN ('confirmed', 'du_kien')", name="confidence_valid"),
        db.CheckConstraint("(course_id IS NULL) <> (skill_id IS NULL)", name="course_or_skill"),
    )


class LearningResource(MockMixin, db.Model):
    __tablename__ = "learning_resources"
    id = pk()
    title = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(16), nullable=False)
    topic = db.Column(db.String(64), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    source_name = db.Column(db.String(255), nullable=False)
    source_url = db.Column(db.String(512))
    scope_cohort = db.Column(db.String(16))
    scope_program_id = fk("programs.id", nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False)
    __table_args__ = (
        db.CheckConstraint("type IN ('quy_dinh', 'faq', 'hoc_lieu', 'ky_nang')", name="type_valid"),
    )


class RiskActionTemplate(MockMixin, db.Model):
    __tablename__ = "risk_action_templates"
    id = pk()
    rule_code = db.Column(db.String(32), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    __table_args__ = (db.UniqueConstraint("rule_code", "order"),)


class ImprovementPlan(MockMixin, db.Model):
    __tablename__ = "improvement_plans"
    id = pk()
    student_id = fk("students.id", index=True)
    title = db.Column(db.String(255), nullable=False)
    source_rule_codes = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(16), nullable=False, default="active")
    created_at = db.Column(db.DateTime, nullable=False)
    __table_args__ = (
        db.CheckConstraint("status IN ('active', 'done', 'archived')", name="status_valid"),
    )


class ImprovementPlanItem(MockMixin, db.Model):
    __tablename__ = "improvement_plan_items"
    id = pk()
    plan_id = fk("improvement_plans.id", index=True)
    title = db.Column(db.String(255), nullable=False)
    due_date = db.Column(db.Date)
    done_at = db.Column(db.DateTime)
    order = db.Column(db.Integer, nullable=False)


class SupportCategory(MockMixin, db.Model):
    __tablename__ = "support_categories"
    id = pk()
    name = db.Column(db.String(64), nullable=False, unique=True)


class SupportStaffCategory(MockMixin, db.Model):
    __tablename__ = "support_staff_categories"
    id = pk()
    user_id = fk("users.id")
    category_id = fk("support_categories.id")
    __table_args__ = (db.UniqueConstraint("user_id", "category_id"),)


class SupportRequest(MockMixin, db.Model):
    __tablename__ = "support_requests"
    id = pk()
    code = db.Column(db.String(32), nullable=False, unique=True)
    student_id = fk("students.id", index=True)
    category_id = fk("support_categories.id", index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(16), nullable=False, default="new")
    assigned_to = fk("users.id", nullable=True)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('new', 'in_progress', 'need_info', 'done')", name="status_valid"
        ),
    )


class SupportMessage(MockMixin, db.Model):
    __tablename__ = "support_messages"
    id = pk()
    request_id = fk("support_requests.id", index=True)
    author_id = fk("users.id")
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)


class SupportAttachment(MockMixin, db.Model):
    __tablename__ = "support_attachments"
    id = pk()
    message_id = fk("support_messages.id", index=True)
    stored_name = db.Column(db.String(128), nullable=False, unique=True)
    original_name = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(64), nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False)
    sha256 = db.Column(db.String(64), nullable=False)
    __table_args__ = (db.CheckConstraint("size_bytes > 0", name="size_positive"),)
