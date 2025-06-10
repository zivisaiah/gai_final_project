#!/usr/bin/env python3
"""
Deployment Setup Script for Streamlit Cloud
Prepares environment and validates configuration for cloud deployment
"""

import os
import sys
import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import toml
import requests
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeploymentSetup:
    """Handles deployment preparation and validation for Streamlit Cloud"""
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.deployment_dir = self.project_root / "deployment"
        self.app_dir = self.project_root / "app"
        self.streamlit_dir = self.project_root / "streamlit_app"
        
    def validate_project_structure(self) -> bool:
        """Validate that all required files and directories exist"""
        logger.info("🔍 Validating project structure...")
        
        required_files = [
            "app/__init__.py",
            "app/main.py",
            "streamlit_app/__init__.py", 
            "streamlit_app/streamlit_main.py",
            "requirements.txt",
            ".env.example",
            "README.md"
        ]
        
        required_dirs = [
            "app/modules/agents",
            "app/modules/database", 
            "app/modules/prompts",
            "streamlit_app/components",
            "data",
            "deployment"
        ]
        
        missing_files = []
        missing_dirs = []
        
        # Check files
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)
                
        # Check directories
        for dir_path in required_dirs:
            if not (self.project_root / dir_path).exists():
                missing_dirs.append(dir_path)
        
        if missing_files or missing_dirs:
            logger.error("❌ Missing required files/directories:")
            for f in missing_files:
                logger.error(f"  - File: {f}")
            for d in missing_dirs:
                logger.error(f"  - Directory: {d}")
            return False
            
        logger.info("✅ Project structure validation passed")
        return True
    
    def validate_environment_variables(self) -> bool:
        """Validate required environment variables"""
        logger.info("🔍 Validating environment variables...")
        
        required_env_vars = [
            "OPENAI_API_KEY",
            "DATABASE_URL",
            "VECTOR_STORE_TYPE"
        ]
        
        optional_env_vars = [
            "OPENAI_ASSISTANT_ID",
            "OPENAI_FILE_ID",
            "DEBUG_MODE"
        ]
        
        missing_vars = []
        
        # Check .env.example exists
        env_example = self.project_root / ".env.example"
        if not env_example.exists():
            logger.error("❌ .env.example file not found")
            return False
            
        # Check required variables
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {missing_vars}")
            logger.info("💡 Please set these in Streamlit Cloud secrets or .env file")
            return False
            
        logger.info("✅ Environment variables validation passed")
        return True
    
    def validate_dependencies(self) -> bool:
        """Validate that all dependencies can be imported"""
        logger.info("🔍 Validating dependencies...")
        
        critical_imports = [
            ("streamlit", "streamlit"),
            ("langchain", "langchain"),
            ("openai", "openai"),
            ("sqlalchemy", "sqlalchemy"), 
            ("chromadb", "chromadb"),
            ("pandas", "pandas"),
            ("plotly", "plotly.express")
        ]
        
        failed_imports = []
        
        for package_name, import_name in critical_imports:
            try:
                __import__(import_name)
                logger.info(f"  ✓ {package_name}")
            except ImportError as e:
                failed_imports.append((package_name, str(e)))
                logger.error(f"  ✗ {package_name}: {e}")
        
        if failed_imports:
            logger.error("❌ Failed to import critical dependencies")
            return False
            
        logger.info("✅ Dependencies validation passed")
        return True
    
    def create_streamlit_secrets_template(self) -> None:
        """Create a template for Streamlit Cloud secrets"""
        logger.info("📝 Creating Streamlit secrets template...")
        
        secrets_template = {
            "OPENAI_API_KEY": "your-openai-api-key-here",
            "DATABASE_URL": "sqlite:///./recruitment_bot.db",
            "VECTOR_STORE_TYPE": "openai",
            "OPENAI_ASSISTANT_ID": "your-assistant-id-here",
            "OPENAI_FILE_ID": "your-file-id-here",
            "DEBUG_MODE": "false"
        }
        
        secrets_file = self.deployment_dir / "streamlit_secrets_template.toml"
        
        with open(secrets_file, 'w') as f:
            toml.dump(secrets_template, f)
            
        logger.info(f"✅ Created secrets template: {secrets_file}")
        logger.info("💡 Copy this to Streamlit Cloud App Settings > Secrets")
    
    def optimize_for_cloud(self) -> None:
        """Apply cloud-specific optimizations"""
        logger.info("⚡ Applying cloud optimizations...")
        
        # Create .streamlit directory
        streamlit_config_dir = self.project_root / ".streamlit"
        streamlit_config_dir.mkdir(exist_ok=True)
        
        # Copy configuration file
        config_source = self.deployment_dir / "streamlit_config.toml"
        config_dest = streamlit_config_dir / "config.toml"
        
        if config_source.exists():
            import shutil
            shutil.copy2(config_source, config_dest)
            logger.info(f"✅ Copied Streamlit config to {config_dest}")
        
        # Create packages.txt for system dependencies
        packages_txt = self.project_root / "packages.txt"
        if not packages_txt.exists():
            with open(packages_txt, 'w') as f:
                f.write("# System packages for Streamlit Cloud\n")
                f.write("# Add any system dependencies here\n")
            logger.info("✅ Created packages.txt template")
        
        logger.info("✅ Cloud optimizations applied")
    
    def test_streamlit_app(self) -> bool:
        """Test if the Streamlit app can start without errors"""
        logger.info("🧪 Testing Streamlit app startup...")
        
        try:
            # Import the main Streamlit app
            sys.path.insert(0, str(self.streamlit_dir))
            
            # Test basic imports
            from streamlit_main import main
            logger.info("✅ Streamlit app imports successfully")
            
            # Test configuration loading
            if (self.project_root / ".streamlit" / "config.toml").exists():
                logger.info("✅ Streamlit config found")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Streamlit app test failed: {e}")
            return False
    
    def generate_deployment_report(self) -> Dict:
        """Generate a comprehensive deployment readiness report"""
        logger.info("📊 Generating deployment report...")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "validations": {
                "project_structure": self.validate_project_structure(),
                "environment_variables": self.validate_environment_variables(),
                "dependencies": self.validate_dependencies(),
                "streamlit_app": self.test_streamlit_app()
            },
            "deployment_files": {
                "config": (self.deployment_dir / "streamlit_config.toml").exists(),
                "requirements": (self.deployment_dir / "requirements_streamlit.txt").exists(),
                "secrets_template": (self.deployment_dir / "streamlit_secrets_template.toml").exists()
            },
            "optimization_status": "applied"
        }
        
        # Calculate overall readiness
        all_validations = all(report["validations"].values())
        all_files = all(report["deployment_files"].values())
        
        report["deployment_ready"] = all_validations and all_files
        report["readiness_score"] = (
            sum(report["validations"].values()) + 
            sum(report["deployment_files"].values())
        ) / (len(report["validations"]) + len(report["deployment_files"]))
        
        # Save report
        report_file = self.deployment_dir / "deployment_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"📊 Deployment report saved: {report_file}")
        
        # Print summary
        status = "✅ READY" if report["deployment_ready"] else "❌ NOT READY"
        score = f"{report['readiness_score']:.1%}"
        
        logger.info(f"🚀 Deployment Status: {status} ({score})")
        
        return report
    
    def run_full_setup(self) -> bool:
        """Run complete deployment setup process"""
        logger.info("🚀 Starting deployment setup process...")
        
        try:
            # Create secrets template
            self.create_streamlit_secrets_template()
            
            # Apply optimizations
            self.optimize_for_cloud()
            
            # Generate comprehensive report
            report = self.generate_deployment_report()
            
            if report["deployment_ready"]:
                logger.info("\n🎉 DEPLOYMENT SETUP COMPLETE!")
                logger.info("📋 Next steps:")
                logger.info("  1. Create new app on Streamlit Cloud")
                logger.info("  2. Connect to your GitHub repository")
                logger.info("  3. Set main file path: streamlit_app/streamlit_main.py")
                logger.info("  4. Add secrets from streamlit_secrets_template.toml")
                logger.info("  5. Deploy and test!")
                return True
            else:
                logger.error("\n❌ Deployment setup incomplete")
                logger.info("📋 Please fix the issues above and run again")
                return False
                
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            return False

def main():
    """Main entry point for deployment setup"""
    setup = DeploymentSetup()
    success = setup.run_full_setup()
    
    if success:
        print("\n✅ Deployment setup completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Deployment setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 